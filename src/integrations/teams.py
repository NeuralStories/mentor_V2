import httpx
from src.utils.logger import get_logger

logger = get_logger(__name__)

class TeamsIntegration:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url

    async def send_adaptive_card(self, title: str, text: str) -> bool:
        if not self.webhook_url:
            logger.warning(f"Teams webhook not configured. Mock sending: {title} - {text}")
            return True
            
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": title,
            "sections": [{
                "activityTitle": title,
                "text": text
            }]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error sending Teams message: {e}")
            return False
