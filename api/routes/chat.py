from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from core.agent.main_agent import CarpinteroAgent

router = APIRouter()
agent = CarpinteroAgent()  # Instancia única del agente

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "default"
    user_role: Optional[str] = "general"
    project_id: Optional[str] = None
    location: Optional[str] = "obra"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    sources: List[dict]
    conversation_id: Optional[str] = None

@app_router_post := router.post("/", response_model=ChatResponse)
async def post_chat(req: ChatRequest):
    """Envía un mensaje al asistente y recibe respuesta técnica."""
    try:
        result = await agent.process_message(
            message=req.message,
            session_id=req.session_id,
            user_id=req.user_id,
            user_role=req.user_role,
            project_id=req.project_id,
            location=req.location
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def post_feedback(conversation_id: str, is_positive: bool, comment: str = None):
    # TODO: Implementar guardado de feedback en Supabase
    return {"status": "recorded"}
