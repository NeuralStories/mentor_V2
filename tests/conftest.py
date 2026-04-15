import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from src.main import app
from src.core.engine import MentorEngine
from src.core.memory import ConversationMemory
from src.core.knowledge_base import KnowledgeBase, KBDocument, DocumentType
from src.core.worker_context import WorkerProfile
from src.services.cache_service import CacheService
from src.db.database import get_db


class MockLLMProvider:
    def __init__(self):
        self.call_count = 0
        self.last_messages = None
        self.responses = {}
        self.default_response = "Mock response from Mentor agent."

    def set_response(self, contains: str, response: str):
        self.responses[contains.lower()] = response

    async def generate(self, messages, **kwargs):
        self.call_count += 1
        self.last_messages = messages
        last_user_msg = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_msg = msg["content"].lower()
                break
        for trigger, response in self.responses.items():
            if trigger in last_user_msg:
                return response
        if "clasificador" in str(messages).lower() or "clasifica" in str(messages).lower():
            return '{"category": "hr", "subcategory": "vacaciones", "urgency": "low", "complexity": "simple", "confidence": 0.9, "department_mentioned": "rrhh", "system_mentioned": "", "process_mentioned": "", "is_followup": false, "requires_escalation": false, "escalation_reason": "", "contains_sensitive_data": false, "sensitive_data_type": ""}'
        return self.default_response

    async def generate_stream(self, messages, **kwargs):
        response = await self.generate(messages, **kwargs)
        for word in response.split():
            yield word + " "


@pytest.fixture
def mock_llm():
    return MockLLMProvider()


@pytest.fixture
def memory():
    return ConversationMemory(max_messages=50, use_redis=False)


@pytest.fixture
def cache():
    return CacheService(use_redis=False, max_local_entries=100, default_ttl=60)


@pytest.fixture
def knowledge_base():
    kb = KnowledgeBase()
    kb.add_document(KBDocument(
        doc_id="test-hr-001", title="Política de Vacaciones",
        content="Los empleados con más de 6 meses tienen derecho a vacaciones. Solicitar con 15 días de anticipación en HR Portal. 6 meses a 1 año: 6 días. 1-2 años: 8 días.",
        doc_type=DocumentType.POLICY, department="rrhh", tags=["vacaciones", "descanso", "días libres"],
    ))
    kb.add_document(KBDocument(
        doc_id="test-it-001", title="Reseteo de Contraseña",
        content="Para resetear tu contraseña ingresa a portal.empresa.com/reset. Necesitas tu número de empleado. Nueva contraseña: mínimo 12 caracteres. Mesa de Ayuda: ext. 5000.",
        doc_type=DocumentType.SOP, department="ti", tags=["contraseña", "password", "acceso"],
    ))
    kb.add_document(KBDocument(
        doc_id="test-safety-001", title="Protocolo de Evacuación",
        content="En caso de alarma: mantén la calma, no uses elevadores, sigue rutas de evacuación. Punto de reunión: Estacionamiento Norte. Emergencias: ext. 911 interna.",
        doc_type=DocumentType.SOP, department="seguridad", tags=["emergencia", "evacuación", "seguridad"],
    ))
    return kb


@pytest.fixture
def sample_worker():
    return WorkerProfile(
        worker_id="test-worker-001", name="Juan Pérez", department="ventas",
        role="ejecutivo", location="Oficina CDMX", hire_date="2023-06-15",
    )


@pytest.fixture
def new_employee():
    from datetime import datetime, timedelta
    recent_date = (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%d")
    return WorkerProfile(
        worker_id="test-worker-new", name="María López", department="marketing",
        role="analista", location="Oficina CDMX", hire_date=recent_date,
    )


@pytest.fixture
def engine(mock_llm, memory, knowledge_base, cache):
    return MentorEngine(
        llm_provider=mock_llm, knowledge_base=knowledge_base, memory=memory, cache_service=cache,
    )


@pytest.fixture
def db_session():
    session = AsyncMock()
    # Mock result scalars first
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result
    return session


@pytest.fixture
async def client(db_session):
    # Override get_db
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
