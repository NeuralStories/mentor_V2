from typing import List, Dict
from core.llm.provider import LLMProvider

PROMPT = """
Genera una guía de instalación paso a paso.
Estructura:
- MATERIALES NECESARIOS
- HERRAMIENTAS
- PASOS NUMERADOS
- PUNTOS CRÍTICOS (⚠️)
- VERIFICACIÓN FINAL (✅)

CONSULTA: {query}
MANUAL: {context}

GUÍA:
"""

class GuiaInstalacionTool:
    def __init__(self, retriever, llm=None):
        self.retriever = retriever
        self.llm = llm or LLMProvider.get_fast_llm()

    async def execute(self, query: str, user_role: str, rag_context: List[Dict] = None) -> str:
        ctx_text = "\n".join([r["content"] for r in (rag_context or [])])
        prompt = PROMPT.format(query=query, context=ctx_text)
        res = self.llm.invoke(prompt)
        return res.content if hasattr(res, 'content') else str(res)
