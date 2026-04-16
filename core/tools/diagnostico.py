from typing import List, Dict
from core.llm.provider import LLMProvider

PROMPT = """
Diagnostica el problema reportado. Sé práctico y directo.
Estructura obligatoria:
- PROBLEMA IDENTIFICADO
- CAUSA PROBABLE
- SOLUCIÓN PASO A PASO
- PLAN B (si lo hay)
- PREVENCIÓN

CONSULTA: {query}
CONTEXTO TÉCNICO: {context}

DIAGNÓSTICO:
"""

class DiagnosticoTool:
    def __init__(self, retriever, llm=None):
        self.retriever = retriever
        self.llm = llm or LLMProvider.get_fast_llm()

    async def execute(self, query: str, user_role: str, rag_context: List[Dict] = None) -> str:
        ctx_text = "\n".join([r["content"] for r in (rag_context or [])])
        prompt = PROMPT.format(query=query, context=ctx_text)
        res = self.llm.invoke(prompt)
        return res.content if hasattr(res, 'content') else str(res)
