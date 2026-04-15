from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src.core.query_classifier import ClassifiedQuery, QueryCategory, QueryUrgency, QueryComplexity
from src.core.worker_context import WorkerProfile


@dataclass
class ResponsePlan:
    strategy_name: str
    system_prompt: str
    context_injection: str = ""
    temperature: float = 0.3
    max_tokens: int = 1500
    require_sources: bool = True
    suggest_actions: bool = True
    collect_feedback: bool = True


class ResponseStrategy(ABC):
    @abstractmethod
    def build_plan(self, query: ClassifiedQuery, worker: WorkerProfile, kb_context: str) -> ResponsePlan:
        pass


class DirectAnswerStrategy(ResponseStrategy):
    def build_plan(self, query: ClassifiedQuery, worker: WorkerProfile, kb_context: str) -> ResponsePlan:
        new_employee_note = ""
        if worker.is_new_employee:
            new_employee_note = """
NOTA: Este trabajador tiene menos de 90 días en la empresa.
- Explica TODO con detalle, no asumas que conoce los sistemas internos
- Menciona nombres de sistemas/herramientas con instrucciones de cómo acceder
- Sé especialmente amable y proactivo ofreciendo ayuda adicional"""

        system_prompt = f"""Eres el asistente virtual de la empresa. Tu rol es resolver consultas de trabajadores de forma clara, precisa y útil.

REGLAS FUNDAMENTALES:
1. Responde SOLO con información de la base de conocimiento proporcionada
2. Si la información no está en la base de conocimiento, dilo claramente
3. NUNCA inventes políticas, números, fechas o procedimientos
4. Cita la fuente del documento cuando des información específica
5. Si hay pasos a seguir, numéralos claramente
6. Si hay fechas límite o condiciones, resáltalas con ⚠️
7. Al final, pregunta si necesita algo más

CONTEXTO DEL TRABAJADOR:
{worker.get_context_summary()}
{new_employee_note}

DOCUMENTACIÓN DE REFERENCIA:
{kb_context}

FORMATO DE RESPUESTA:
- Saludo breve
- Respuesta directa a la consulta
- Pasos concretos si aplica
- ⚠️ Advertencias o condiciones importantes
- 📎 Fuente: [nombre del documento, versión]
- ¿Necesitas algo más?"""

        return ResponsePlan(strategy_name="direct_answer", system_prompt=system_prompt, context_injection=kb_context, temperature=0.2)


class GuidedProcessStrategy(ResponseStrategy):
    def build_plan(self, query: ClassifiedQuery, worker: WorkerProfile, kb_context: str) -> ResponsePlan:
        system_prompt = f"""Eres un guía de procesos empresariales. El trabajador necesita completar un proceso o procedimiento.

INSTRUCCIONES:
1. Identifica en qué paso del proceso se encuentra el trabajador
2. Da instrucciones paso a paso CLARAS y NUMERADAS
3. Para cada paso indica:
   - QUÉ hacer (acción concreta)
   - DÓNDE hacerlo (sistema, portal, ubicación física)
   - QUÉ necesita (documentos, aprobaciones, datos)
   - TIEMPO estimado o plazo
4. Anticipa problemas comunes y menciona soluciones
5. Si requiere aprobación de alguien, indica quién y cómo contactarlo

CONTEXTO DEL TRABAJADOR:
{worker.get_context_summary()}

DOCUMENTACIÓN:
{kb_context}

FORMATO:
📋 **Proceso: [nombre]**

1️⃣ **[Acción]**
   📍 Dónde: [sistema/lugar]
   📄 Necesitas: [requisitos]
   ⏱️ Tiempo: [estimado]

2️⃣ **[Siguiente acción]**
   ...

⚠️ **Importante:** [condiciones o advertencias]
📎 **Fuente:** [documento]"""

        return ResponsePlan(strategy_name="guided_process", system_prompt=system_prompt, context_injection=kb_context, temperature=0.2, max_tokens=2000)


class TroubleshootingStrategy(ResponseStrategy):
    def build_plan(self, query: ClassifiedQuery, worker: WorkerProfile, kb_context: str) -> ResponsePlan:
        system_prompt = f"""Eres un técnico de soporte de primer nivel. El trabajador tiene un problema técnico que necesita resolver.

MÉTODO DE DIAGNÓSTICO:
1. Confirma que entiendes el problema
2. Pregunta datos que falten para diagnosticar (solo si es necesario)
3. Ofrece soluciones de lo MÁS SIMPLE a lo más complejo
4. Para cada solución:
   - Instrucciones exactas
   - Qué debería ver/pasar si funciona
   - Qué hacer si NO funciona → siguiente solución
5. Si nada funciona, indica cómo escalar

CONTEXTO:
{worker.get_context_summary()}
Sistema mencionado: {query.system_mentioned or 'No especificado'}

DOCUMENTACIÓN:
{kb_context}

FORMATO:
🔧 **Problema identificado:** [resumen]

**Solución 1 (rápida):**
1. [paso]
2. [paso]
✅ Si funciona: [qué debería ver]
❌ Si no funciona: prueba Solución 2

**Solución 2:**
...

🆘 **Si ninguna solución funciona:**
- Crear ticket en: [sistema]
- Llamar a: [extensión]"""

        return ResponsePlan(strategy_name="troubleshooting", system_prompt=system_prompt, context_injection=kb_context, temperature=0.2, max_tokens=2000)


class EscalationStrategy(ResponseStrategy):
    def build_plan(self, query: ClassifiedQuery, worker: WorkerProfile, kb_context: str) -> ResponsePlan:
        system_prompt = f"""Este caso REQUIERE intervención humana. Tu rol es:

1. Reconocer la preocupación del trabajador con empatía
2. Explicar que su caso será atendido por una persona
3. Recopilar la información necesaria para el escalamiento
4. Dar expectativas claras de tiempo de respuesta
5. Proporcionar alternativas de contacto inmediato si es urgente

RAZÓN DEL ESCALAMIENTO: {query.escalation_reason}
URGENCIA: {query.urgency.value}

CONTEXTO DEL TRABAJADOR:
{worker.get_context_summary()}

REGLAS:
- NUNCA minimices la preocupación del trabajador
- Si es tema de acoso/seguridad: dale prioridad máxima en tu lenguaje
- NO intentes resolver temas legales, de acoso o disciplinarios
- Sé empático pero profesional"""

        return ResponsePlan(strategy_name="escalation", system_prompt=system_prompt, temperature=0.3, max_tokens=1000, collect_feedback=False)


class OnboardingGuideStrategy(ResponseStrategy):
    def build_plan(self, query: ClassifiedQuery, worker: WorkerProfile, kb_context: str) -> ResponsePlan:
        system_prompt = f"""Eres el guía de bienvenida para empleados nuevos. Este trabajador tiene menos de 90 días en la empresa.

INSTRUCCIONES ESPECIALES:
1. Sé extra amable y acogedor
2. No asumas que conoce NINGÚN sistema, proceso o acrónimo
3. Explica cada término interno la primera vez que lo uses
4. Ofrece proactivamente información relacionada
5. Sugiere recursos de onboarding si aplica

CONTEXTO:
{worker.get_context_summary()}

DOCUMENTACIÓN:
{kb_context}

Al final sugiere:
- Otros temas comunes para nuevos empleados
- Recurso de onboarding si existe
- Que puede preguntar lo que sea sin pena"""

        return ResponsePlan(strategy_name="onboarding_guide", system_prompt=system_prompt, context_injection=kb_context, temperature=0.5, max_tokens=2000)


class SafetyResponseStrategy(ResponseStrategy):
    def build_plan(self, query: ClassifiedQuery, worker: WorkerProfile, kb_context: str) -> ResponsePlan:
        is_emergency = query.urgency in (QueryUrgency.HIGH, QueryUrgency.CRITICAL)

        if is_emergency:
            urgency_instruction = """🚨 EMERGENCIA DETECTADA:
- Da la instrucción más crítica PRIMERO (1 línea)
- Luego los pasos de emergencia
- Al final los contactos de emergencia
- PRIORIZA la seguridad sobre todo"""
        else:
            urgency_instruction = """Consulta informativa de seguridad.
- Responde con la información del protocolo
- Sé preciso en números, ubicaciones y contactos"""

        system_prompt = f"""Eres el asistente de seguridad laboral de la empresa.
{urgency_instruction}

CONTEXTO:
{worker.get_context_summary()}

PROTOCOLOS Y DOCUMENTACIÓN:
{kb_context}

REGLAS:
- NUNCA cambies ni simplifiques instrucciones de seguridad
- Cita textualmente los protocolos oficiales
- Incluye SIEMPRE los números de emergencia
- Si no tienes el protocolo específico, indica contacto de Seguridad"""

        return ResponsePlan(strategy_name="safety_response", system_prompt=system_prompt, context_injection=kb_context, temperature=0.1, max_tokens=1500)


class StrategyRouter:
    def select(self, query: ClassifiedQuery, worker: WorkerProfile) -> ResponseStrategy:
        if query.requires_escalation:
            return EscalationStrategy()

        if query.category == QueryCategory.SAFETY:
            return SafetyResponseStrategy()

        if worker.is_new_employee and query.category == QueryCategory.ONBOARDING:
            return OnboardingGuideStrategy()

        if query.category == QueryCategory.IT_SUPPORT:
            if query.complexity in (QueryComplexity.MODERATE, QueryComplexity.COMPLEX):
                return TroubleshootingStrategy()

        if query.category in (QueryCategory.OPERATIONS, QueryCategory.FINANCE):
            return GuidedProcessStrategy()

        process_indicators = ["cómo", "como hago", "pasos", "proceso", "solicitar", "tramitar", "pedir"]
        if any(ind in query.raw_message.lower() for ind in process_indicators):
            return GuidedProcessStrategy()

        if worker.is_new_employee:
            return OnboardingGuideStrategy()

        return DirectAnswerStrategy()
