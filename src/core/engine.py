"""Motor principal del agente MENTOR. Orquesta el pipeline completo de consultas."""

import time
import uuid
from typing import Optional, Any
from dataclasses import dataclass, field

from src.core.query_classifier import QueryClassifier, ClassifiedQuery, QueryCategory, QueryUrgency, QueryComplexity
from src.core.worker_context import WorkerProfile
from src.core.knowledge_base import KnowledgeBase
from src.core.response_strategies import StrategyRouter
from src.core.memory import ConversationMemory
from src.core.escalation import EscalationManager
from src.core.llm_providers import BaseLLMProvider, get_llm_provider
from src.db.repositories import WorkerRepository, TicketRepository
from src.services.cache_service import CacheService
from src.integrations.slack import SlackIntegration
from src.integrations.teams import TeamsIntegration
from src.integrations.webhooks import WebhookIntegration
from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Límites de historial adaptativo según complejidad de consulta
HISTORY_LIMITS = {
    QueryComplexity.SIMPLE: 4,
    QueryComplexity.MODERATE: 8,
    QueryComplexity.COMPLEX: 12,
    QueryComplexity.REQUIRES_HUMAN: 16,
}


@dataclass
class AgentResponse:
    """Respuesta generada por el agente MENTOR."""
    content: str
    session_id: str
    strategy_used: str = ""
    category: str = ""
    urgency: str = ""
    sources_used: list[str] = field(default_factory=list)
    was_escalated: bool = False
    escalation_ticket: Optional[str] = None
    suggested_actions: list[str] = field(default_factory=list)
    collect_feedback: bool = True
    latency_ms: float = 0.0
    metadata: dict = field(default_factory=dict)


class MentorEngine:
    """
    Motor principal del agente empresarial MENTOR.
    Integra clasificacion, KB, estrategias, cache, escalamiento y notificaciones.
    """

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
        memory: Optional[ConversationMemory] = None,
        escalation_manager: Optional[EscalationManager] = None,
        cache_service: Optional[CacheService] = None,
    ):
        settings = get_settings()

        # Core
        self.llm = llm_provider or get_llm_provider()
        self.kb = knowledge_base or KnowledgeBase()
        self.memory = memory or ConversationMemory()
        self.classifier = QueryClassifier(self.llm)
        self.strategy_router = StrategyRouter()
        self.cache = cache_service or CacheService()

        # Integraciones: instanciar Slack/Teams/Webhook desde config
        slack = SlackIntegration(webhook_url=settings.slack_webhook_url) if settings.slack_webhook_url else None
        teams = TeamsIntegration(webhook_url=settings.teams_webhook_url) if settings.teams_webhook_url else None
        webhook = WebhookIntegration() if settings.escalation_webhook_url else None

        # Escalamiento con integraciones conectadas
        self.escalation = escalation_manager or EscalationManager(
            slack=slack, teams=teams, webhook=webhook,
        )

        # Workers en memoria
        self._workers: dict[str, WorkerProfile] = {}

        logger.info("MentorEngine (Enterprise Agent) initialized")
        if slack:
            logger.info("Slack integration: ACTIVE")
        if teams:
            logger.info("Teams integration: ACTIVE")
        if webhook:
            logger.info("Webhook integration: ACTIVE")

    async def register_worker(self, profile: WorkerProfile, db_session: Optional[Any] = None) -> None:
        """Registra un trabajador en el sistema."""
        self._workers[profile.worker_id] = profile
        if db_session:
            repo = WorkerRepository(db_session)
            await repo.save(profile)
        logger.info(f"Worker registered: {profile.worker_id} ({profile.department})")

    async def _get_worker(self, worker_id: str, db_session: Optional[Any] = None) -> WorkerProfile:
        """Obtiene un trabajador de memoria o DB, o lo crea."""
        # 1. Intentar memoria
        if worker_id in self._workers:
            return self._workers[worker_id]
        
        # 2. Intentar DB
        if db_session:
            repo = WorkerRepository(db_session)
            profile = await repo.get(worker_id)
            if profile:
                self._workers[worker_id] = profile
                return profile
        
        # 3. Crear nuevo si no existe
        new_profile = WorkerProfile(worker_id=worker_id)
        self._workers[worker_id] = new_profile
        return new_profile

    async def handle_query(
        self, message: str, worker_id: str, session_id: Optional[str] = None, db_session: Optional[Any] = None
    ) -> AgentResponse:
        """
        Pipeline completo de procesamiento de consulta:
        1. Clasificar  2. Datos sensibles  3. Cache  4. KB Search
        5. Estrategia  6. LLM Generate  7. Escalamiento  8. Registrar  9. Cache save
        """
        start_time = time.perf_counter()
        session_id = session_id or f"{worker_id}-{uuid.uuid4().hex[:8]}"
        worker = await self._get_worker(worker_id, db_session)
        
        # Obtener historial inicial corto para clasificacion
        history = await self.memory.get_history(session_id, limit=4)

        # FASE 1: CLASIFICAR
        classified = await self.classifier.classify(
            message=message,
            history=history,
            worker_context={"department": worker.department, "role": worker.role},
        )
        logger.info(
            f"Query classified: category={classified.category.value}, "
            f"urgency={classified.urgency.value}, escalation={classified.requires_escalation}"
        )

        # FASE 2: DATOS SENSIBLES
        if classified.contains_sensitive_data:
            logger.warning(f"Sensitive data detected from worker {worker_id}")
            safe_message = self.classifier._redact_sensitive(message)
        else:
            safe_message = message

        # FASE 3: CACHE
        cached = await self.cache.get(query=message, category=classified.category.value)
        if cached and not classified.requires_escalation:
            latency = (time.perf_counter() - start_time) * 1000
            await self.memory.add_message(session_id, "user", safe_message)
            await self.memory.add_message(session_id, "assistant", cached["content"])
            worker.record_query(classified.category.value)
            return AgentResponse(
                content=cached["content"],
                session_id=session_id,
                strategy_used=cached.get("strategy", "cache"),
                category=classified.category.value,
                urgency=classified.urgency.value,
                sources_used=cached.get("sources", []),
                suggested_actions=self._generate_actions(classified),
                latency_ms=round(latency, 2),
                metadata={"cache_hit": True},
            )

        # FASE 4: BUSCAR EN KB
        kb_results = await self.kb.search(
            query=message,
            department=self._map_category_to_department(classified.category),
            max_results=5,
            access_level=worker.access_level,
        )
        logger.info(f"KB search: {kb_results.total_found} documents found")

        # FASE 5: SELECCIONAR ESTRATEGIA
        strategy = self.strategy_router.select(classified, worker)
        plan = strategy.build_plan(
            query=classified,
            worker=worker,
            kb_context=kb_results.context if kb_results.total_found > 0
            else "No se encontro documentacion especifica para esta consulta.",
        )
        logger.info(f"Strategy selected: {plan.strategy_name}")

        # FASE 5.5: HISTORIAL ADAPTATIVO
        hist_limit = HISTORY_LIMITS.get(classified.complexity, 6)
        full_history = await self.memory.get_history(session_id, limit=hist_limit)

        # FASE 6: GENERAR RESPUESTA CON LLM
        messages = [{"role": "system", "content": plan.system_prompt}]
        messages.extend(full_history)
        messages.append({"role": "user", "content": message})

        try:
            response_content = await self.llm.generate(
                messages=messages,
                temperature=plan.temperature,
                max_tokens=plan.max_tokens,
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            response_content = (
                "Lo siento, estoy teniendo dificultades tecnicas. "
                "Por favor intenta de nuevo en unos minutos o contacta a "
                "Mesa de Ayuda en la extension 5000."
            )

        # FASE 7: ESCALAMIENTO
        escalation_ticket = None
        was_escalated = False
        if classified.requires_escalation:
            # Pasar repositorio al manager temporalmente si hay sesión
            if db_session:
                self.escalation._repo = TicketRepository(db_session)
            
            escalation_ticket = await self.escalation.create_ticket(
                worker=worker,
                query=classified,
                conversation_history=full_history,
                original_message=message,
            )
            was_escalated = True

        # FASE 8: REGISTRAR Y GUARDAR
        await self.memory.add_message(session_id, "user", safe_message)
        await self.memory.add_message(session_id, "assistant", response_content)
        worker.record_query(classified.category.value)
        
        # Guardar cambios en trabajador si hay sesión
        if db_session:
            await WorkerRepository(db_session).save(worker)

        sources = [doc.title for doc in kb_results.documents]

        # FASE 9: GUARDAR EN CACHE
        if not classified.requires_escalation and classified.confidence >= 0.6:
            await self.cache.set(
                query=message,
                category=classified.category.value,
                response_content=response_content,
                sources=sources,
                strategy=plan.strategy_name,
            )

        latency = (time.perf_counter() - start_time) * 1000

        return AgentResponse(
            content=response_content,
            session_id=session_id,
            strategy_used=plan.strategy_name,
            category=classified.category.value,
            urgency=classified.urgency.value,
            sources_used=sources,
            was_escalated=was_escalated,
            escalation_ticket=escalation_ticket,
            suggested_actions=self._generate_actions(classified),
            collect_feedback=plan.collect_feedback,
            latency_ms=round(latency, 2),
            metadata={
                "complexity": classified.complexity.value,
                "confidence": classified.confidence,
                "kb_documents_found": kb_results.total_found,
                "worker_department": worker.department,
                "is_new_employee": worker.is_new_employee,
                "cache_hit": False,
            },
        )

    async def handle_feedback(
        self, session_id: str, worker_id: str, score: int, comment: Optional[str] = None, db_session: Optional[Any] = None
    ) -> dict:
        """Registra feedback de satisfaccion del trabajador."""
        worker = await self._get_worker(worker_id, db_session)
        worker.record_satisfaction(score)
        
        if db_session:
            await WorkerRepository(db_session).save(worker)
            
        feedback_data = {
            "session_id": session_id,
            "worker_id": worker_id,
            "score": score,
            "comment": comment,
            "recorded": True,
            "avg_satisfaction": worker.avg_satisfaction,
        }
        logger.info(
            f"Feedback received: worker={worker_id}, score={score}, "
            f"avg={worker.avg_satisfaction:.2f}"
        )
        if score <= 2:
            logger.warning(f"Low satisfaction from worker {worker_id}: {score}/5")
        return feedback_data

    async def get_analytics(self) -> dict:
        """Genera analíticas generales del agente."""
        total_workers = len(self._workers)
        total_queries = sum(w.total_queries for w in self._workers.values())

        category_counts: dict[str, int] = {}
        for worker in self._workers.values():
            for cat, count in worker.queries_by_category.items():
                category_counts[cat] = category_counts.get(cat, 0) + count

        all_scores = []
        for worker in self._workers.values():
            all_scores.extend(worker.satisfaction_scores)
        avg_satisfaction = sum(all_scores) / len(all_scores) if all_scores else 0

        return {
            "total_workers_served": total_workers,
            "total_queries": total_queries,
            "queries_by_category": category_counts,
            "avg_satisfaction": round(avg_satisfaction, 2),
            "kb_stats": self.kb.get_stats(),
            "cache_stats": self.cache.get_stats(),
            "escalation_stats": self.escalation.get_stats(),
        }

    def _map_category_to_department(self, category: QueryCategory) -> str:
        """Mapea categoría de consulta al departamento de la KB."""
        mapping = {
            QueryCategory.HR: "rrhh",
            QueryCategory.IT_SUPPORT: "ti",
            QueryCategory.OPERATIONS: "operaciones",
            QueryCategory.POLICY: "rrhh",
            QueryCategory.SAFETY: "seguridad",
            QueryCategory.ONBOARDING: "rrhh",
            QueryCategory.TOOLS: "ti",
            QueryCategory.COMPLIANCE: "legal",
            QueryCategory.FACILITIES: "administracion",
            QueryCategory.FINANCE: "finanzas",
        }
        return mapping.get(category, "")

    def _generate_actions(self, classified: ClassifiedQuery) -> list[str]:
        """Genera acciones sugeridas según la categoría de la consulta."""
        actions = []
        category_actions = {
            QueryCategory.HR: ["HR Portal: portal.empresa.com/hr", "RRHH: ext. 3000"],
            QueryCategory.IT_SUPPORT: ["Crear ticket en ServiceNow", "Mesa de Ayuda: ext. 5000"],
            QueryCategory.FINANCE: ["SAP Concur: concur.empresa.com", "Finanzas: ext. 4000"],
            QueryCategory.SAFETY: ["Emergencias: ext. 911 interna", "Reportar: safety.empresa.com"],
        }
        if classified.category in category_actions:
            actions.extend(category_actions[classified.category])
        return actions
