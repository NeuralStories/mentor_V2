from typing import List, Dict
from core.llm.provider import LLMProvider

PROMPT = """
Actúa como un manual técnico. Extrae una respuesta precisa basada EXCLUSIVAMENTE en el contexto proporcionado.
Si hay medidas, especifícalas. Si hay advertencias, lístalas.

CONSULTA: {query}
CONTEXTO: {context}

RESPUESTA TÉCNICA:
"""

class ConsultaTecnicaTool:
    def __init__(self, retriever, llm=None):
        self.retriever = retriever
        self.llm = llm or LLMProvider.get_fast_llm()

    async def execute(self, query: str, user_role: str, rag_context: List[Dict] = None) -> str:
        ctx_text = "\n".join([r["content"] for r in (rag_context or [])])
        if not ctx_text: return "No hay información técnica específica en los manuales."
        
        prompt = PROMPT.format(query=query, context=ctx_text)
        res = self.llm.invoke(prompt)
        return res.content if hasattr(res, 'content') else str(res)
