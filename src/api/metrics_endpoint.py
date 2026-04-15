from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from src.services.metrics import generate_latest_metrics

router = APIRouter(tags=["metrics"])

@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return generate_latest_metrics()
