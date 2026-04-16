from fastapi import APIRouter, UploadFile, File, Form
import shutil
import os
import whisper
from core.agent.main_agent import CarpinteroAgent

router = APIRouter()
agent = CarpinteroAgent()

# Carga perezosa (lazy) del modelo Whisper
_whisper_model = None

def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from core.config import settings
        _whisper_model = whisper.load_model(settings.WHISPER_MODEL)
    return _whisper_model

@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio a texto usando Whisper local."""
    temp_file = f"temp_{audio.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
    
    try:
        model = get_whisper()
        result = model.transcribe(temp_file)
        return {"text": result["text"]}
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

@router.post("/chat-voice")
async def chat_voice(
    audio: UploadFile = File(...),
    session_id: str = Form(None),
    user_id: str = Form("default"),
    user_role: str = Form("general"),
    location: str = Form("obra")
):
    """Proceso completo: Voz -> Texto -> Agente -> Respuesta."""
    # 1. Transcribir
    transcription = await transcribe_audio(audio)
    text = transcription["text"]
    
    # 2. Procesar con agente
    result = await agent.process_message(
        message=text,
        session_id=session_id,
        user_id=user_id,
        user_role=user_role,
        location=location
    )
    
    # 3. Incluir la transcripción en la respuesta para el UI
    result["transcription"] = text
    return result
