from abc import ABC, abstractmethod
from typing import AsyncGenerator
from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict], **kwargs) -> str:
        pass

    @abstractmethod
    async def generate_stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        pass


class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate(self, messages: list[dict], **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=kwargs.get("model", settings.model_name),
            messages=messages,
            max_tokens=kwargs.get("max_tokens", settings.max_tokens),
            temperature=kwargs.get("temperature", settings.temperature),
        )
        return response.choices[0].message.content

    async def generate_stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        stream = await self.client.chat.completions.create(
            model=kwargs.get("model", settings.model_name),
            messages=messages,
            max_tokens=kwargs.get("max_tokens", settings.max_tokens),
            temperature=kwargs.get("temperature", settings.temperature),
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicProvider(BaseLLMProvider):
    def __init__(self):
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate(self, messages: list[dict], **kwargs) -> str:
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append(msg)
        response = await self.client.messages.create(
            model=kwargs.get("model", "claude-3-5-sonnet-20241022"),
            max_tokens=kwargs.get("max_tokens", settings.max_tokens),
            system=system_msg,
            messages=chat_messages,
        )
        return response.content[0].text

    async def generate_stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append(msg)
        async with self.client.messages.stream(
            model=kwargs.get("model", "claude-3-5-sonnet-20241022"),
            max_tokens=kwargs.get("max_tokens", settings.max_tokens),
            system=system_msg,
            messages=chat_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text


class OllamaProvider(BaseLLMProvider):
    def __init__(self):
        import httpx
        self.base_url = settings.ollama_base_url
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(self, messages: list[dict], **kwargs) -> str:
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json={"model": kwargs.get("model", settings.model_name), "messages": messages, "stream": False},
        )
        return response.json()["message"]["content"]

    async def generate_stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        import json as json_lib
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={"model": kwargs.get("model", settings.model_name), "messages": messages, "stream": True},
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json_lib.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]


def get_llm_provider() -> BaseLLMProvider:
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
    }
    provider_class = providers.get(settings.llm_provider)
    if not provider_class:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    return provider_class()
