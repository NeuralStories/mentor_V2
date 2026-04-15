import httpx
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SlackIntegration:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url

    async def send_message(self, channel: str, message: str) -> bool:
        if not self.webhook_url:
            logger.warning(f"Slack webhook not configured. Mock sending to {channel}: {message}")
            return True
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json={"channel": channel, "text": message}
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return False
