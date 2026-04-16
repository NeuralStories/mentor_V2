from typing import List, Dict
from core.llm.provider import LLMProvider

PROMPT = """
Valida si la acción propuesta por el usuario es correcta técnicamente.
Responde con:
✅ CORRECTO + explicación
⚠️ ATENCIÓN + qué revisar
❌ INCORRECTO + por qué y qué hacer

CONSULTA/ACCIÓN: {query}
REGLAS TÉCNICAS: {context}

VALIDACIÓN:
"""

class VerificacionTool:
    def __init__(self, retriever, llm=None):
        self.retriever = retriever
        self.llm = llm or LLMProvider.get_fast_llm()

    async def execute(self, query: str, user_role: str, rag_context: List[Dict] = None) -> str:
        ctx_text = "\n".join([r["content"] for r in (rag_context or [])])
        prompt = PROMPT.format(query=query, context=ctx_text)
        res = self.llm.invoke(prompt)
        return res.content if hasattr(res, 'content') else str(res)
