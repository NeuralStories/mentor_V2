import httpx
from src.utils.logger import get_logger

logger = get_logger(__name__)

class WebhookIntegration:
    async def trigger(self, url: str, payload: dict) -> bool:
        logger.info(f"Triggering webhook to {url}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=5.0)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error triggering webhook {url}: {e}")
            return False
