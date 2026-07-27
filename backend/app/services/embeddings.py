"""Embedding adapter. Swapping providers (Voyage, local model) means editing this file only."""

from typing import Protocol

from openai import AsyncOpenAI

from app.config import settings


class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbeddings:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(
            model=settings.embedding_model, input=texts
        )
        return [item.embedding for item in resp.data]


_provider: EmbeddingProvider | None = None


def get_provider() -> EmbeddingProvider:
    global _provider
    if _provider is None:
        _provider = OpenAIEmbeddings()
    return _provider
