from typing import Sequence

from app.core.config import Settings, settings
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.registry import EmbeddingProviderRegistry


class EmbeddingService:
    dimension: int = 384
    model_name: str = "local-hashing-384-v1"

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
        configured: Settings = settings,
    ) -> None:
        resolution = (
            None
            if provider is not None
            else EmbeddingProviderRegistry(configured).resolve()
        )
        self.provider = provider or resolution.provider
        self.identity = self.provider.identity
        self.dimension = self.identity.dimension
        self.model_name = self.identity.model
        self.fallback_category = (
            resolution.fallback_category if resolution is not None else None
        )

    def embed_text(
        self,
        text: str,
    ) -> list[float]:
        return self.provider.embed_query(text)

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self.provider.embed_documents(texts)
