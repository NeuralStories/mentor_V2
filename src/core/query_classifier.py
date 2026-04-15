from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import json
import re


class QueryCategory(str, Enum):
    HR = "hr"
    IT_SUPPORT = "it_support"
    OPERATIONS = "operations"
    POLICY = "policy"
    SAFETY = "safety"
    ONBOARDING = "onboarding"
    TOOLS = "tools"
    COMPLIANCE = "compliance"
    FACILITIES = "facilities"
    FINANCE = "finance"
    ESCALATION = "escalation"
    GENERAL = "general"


class QueryUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class QueryComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    REQUIRES_HUMAN = "requires_human"


@dataclass
class ClassifiedQuery:
    category: QueryCategory
    subcategory: str = ""
    urgency: QueryUrgency = QueryUrgency.MEDIUM
    complexity: QueryComplexity = QueryComplexity.SIMPLE
    confidence: float = 0.0
    department_mentioned: str = ""
    system_mentioned: str = ""
    process_mentioned: str = ""
    people_mentioned: list[str] = field(default_factory=list)
    dates_mentioned: list[str] = field(default_factory=list)
    is_followup: bool = False
    requires_escalation: bool = False
    escalation_reason: str = ""
    contains_sensitive_data: bool = False
    sensitive_data_type: str = ""
    raw_message: str = ""


class QueryClassifier:
    CLASSIFICATION_PROMPT = """Eres un clasificador de consultas internas de empresa.
Analiza el mensaje de un trabajador y clasifícalo.

MENSAJE: "{message}"

CONTEXTO DE CONVERSACIÓN:
{history_summary}

INFORMACIÓN DEL TRABAJADOR:
- Departamento: {department}
- Rol: {role}

Responde SOLO con JSON válido:
{{
    "category": "<hr|it_support|operations|policy|safety|onboarding|tools|compliance|facilities|finance|escalation|general>",
    "subcategory": "<subcategoría específica>",
    "urgency": "<low|medium|high|critical>",
    "complexity": "<simple|moderate|complex|requires_human>",
    "confidence": <0.0-1.0>,
    "department_mentioned": "<departamento mencionado o vacío>",
    "system_mentioned": "<sistema/herramienta mencionada o vacío>",
    "process_mentioned": "<proceso mencionado o vacío>",
    "is_followup": <true|false>,
    "requires_escalation": <true|false>,
    "escalation_reason": "<razón si requiere escalamiento>",
    "contains_sensitive_data": <true|false>,
    "sensitive_data_type": "<tipo de dato sensible si aplica>"
}}

CRITERIOS DE URGENCIA:
- low: consulta informativa, no bloquea trabajo
- medium: necesita respuesta en horas
- high: bloquea trabajo del empleado AHORA
- critical: emergencia de seguridad, sistema crítico caído, incidente

CRITERIOS DE ESCALAMIENTO:
- Quejas formales → escalar
- Temas legales → escalar
- Acoso/discriminación → escalar SIEMPRE como critical
- El trabajador pide hablar con un humano → escalar"""

    SENSITIVE_PATTERNS = [
        r'\b\d{3}-?\d{2}-?\d{4}\b',
        r'\b\d{16}\b',
        r'\b[A-Z]{3,4}\d{6}[A-Z0-9]{3}\b',
        r'\bpassword\s*[:=]\s*\S+',
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    ]

    def __init__(self, llm_provider):
        self.llm = llm_provider

    async def classify(self, message: str, history: list[dict] = None, worker_context: dict = None) -> ClassifiedQuery:
        worker_context = worker_context or {}
        history_summary = self._summarize_history(history or [])
        sensitive_check = self._check_sensitive_data(message)

        prompt = self.CLASSIFICATION_PROMPT.format(
            message=self._redact_sensitive(message),
            history_summary=history_summary,
            department=worker_context.get("department", "No especificado"),
            role=worker_context.get("role", "No especificado"),
        )

        try:
            raw_response = await self.llm.generate(
                messages=[
                    {"role": "system", "content": "Clasificador de consultas empresariales. Responde SOLO JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=400,
            )
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]

            data = json.loads(cleaned)
            result = ClassifiedQuery(
                category=QueryCategory(data.get("category", "general")),
                subcategory=data.get("subcategory", ""),
                urgency=QueryUrgency(data.get("urgency", "medium")),
                complexity=QueryComplexity(data.get("complexity", "simple")),
                confidence=float(data.get("confidence", 0.5)),
                department_mentioned=data.get("department_mentioned", ""),
                system_mentioned=data.get("system_mentioned", ""),
                process_mentioned=data.get("process_mentioned", ""),
                is_followup=bool(data.get("is_followup", False)),
                requires_escalation=bool(data.get("requires_escalation", False)),
                escalation_reason=data.get("escalation_reason", ""),
                contains_sensitive_data=sensitive_check["found"],
                sensitive_data_type=sensitive_check.get("type", ""),
                raw_message=message,
            )
            result = self._apply_escalation_rules(result)
            return result

        except (json.JSONDecodeError, ValueError, KeyError):
            return self._rule_based_fallback(message, sensitive_check)

    def _check_sensitive_data(self, message: str) -> dict:
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return {"found": True, "type": "personal_data"}
        return {"found": False}

    def _redact_sensitive(self, message: str) -> str:
        redacted = message
        for pattern in self.SENSITIVE_PATTERNS:
            redacted = re.sub(pattern, "[DATO_REDACTADO]", redacted, flags=re.IGNORECASE)
        return redacted

    def _apply_escalation_rules(self, query: ClassifiedQuery) -> ClassifiedQuery:
        msg_lower = query.raw_message.lower()
        force_keywords = [
            "acoso", "discriminación", "amenaza", "violencia",
            "demanda", "abogado", "legal", "denuncia",
            "quiero hablar con alguien", "hablar con un humano",
            "supervisor", "gerente", "queja formal",
        ]
        if any(kw in msg_lower for kw in force_keywords):
            query.requires_escalation = True
            query.urgency = QueryUrgency.CRITICAL
            query.complexity = QueryComplexity.REQUIRES_HUMAN
            if not query.escalation_reason:
                query.escalation_reason = "Tema sensible detectado automáticamente"
        return query

    def _summarize_history(self, history: list[dict]) -> str:
        if not history:
            return "Primera consulta de la conversación."
        last = history[-4:]
        parts = []
        for msg in last:
            role = "Trabajador" if msg["role"] == "user" else "Agente"
            content = msg["content"][:200]
            parts.append(f"  {role}: {content}")
        return "\n".join(parts)

    def _rule_based_fallback(self, message: str, sensitive_check: dict) -> ClassifiedQuery:
        msg_lower = message.lower()
        category = QueryCategory.GENERAL
        urgency = QueryUrgency.MEDIUM

        hr_keywords = ["vacaciones", "nómina", "sueldo", "salario", "permiso", "incapacidad", "baja", "contrato", "liquidación", "aguinaldo", "beneficio", "seguro", "prestación", "horario", "turno"]
        it_keywords = ["contraseña", "password", "acceso", "sistema", "computadora", "correo", "email", "vpn", "internet", "impresora", "software", "instalar", "actualizar", "lento", "no funciona", "error"]
        safety_keywords = ["accidente", "emergencia", "incendio", "evacuación", "primeros auxilios", "seguridad", "peligro", "riesgo"]
        ops_keywords = ["proceso", "procedimiento", "paso a paso", "cómo se hace", "formulario", "aprobación", "flujo", "workflow"]
        finance_keywords = ["reembolso", "gasto", "factura", "viáticos", "presupuesto"]

        if any(kw in msg_lower for kw in safety_keywords):
            category = QueryCategory.SAFETY
            urgency = QueryUrgency.HIGH
        elif any(kw in msg_lower for kw in hr_keywords):
            category = QueryCategory.HR
        elif any(kw in msg_lower for kw in it_keywords):
            category = QueryCategory.IT_SUPPORT
        elif any(kw in msg_lower for kw in finance_keywords):
            category = QueryCategory.FINANCE
        elif any(kw in msg_lower for kw in ops_keywords):
            category = QueryCategory.OPERATIONS

        return ClassifiedQuery(
            category=category,
            urgency=urgency,
            confidence=0.4,
            contains_sensitive_data=sensitive_check["found"],
            sensitive_data_type=sensitive_check.get("type", ""),
            raw_message=message,
        )
