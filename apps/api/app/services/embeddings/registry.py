from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from app.core.config import Settings
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.hashing import HashingEmbeddingProvider
from app.services.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)


@dataclass(frozen=True)
class EmbeddingResolution:
    provider: EmbeddingProvider = field(repr=False)
    requested_provider: str
    fallback_category: str | None = None

    @property
    def effective_provider(self) -> str:
        return self.provider.identity.provider


class EmbeddingProviderRegistry:
    _allowlist = {"hashing", "sentence_transformer"}

    def __init__(
        self,
        configured: Settings,
        *,
        semantic_factory: Callable[..., EmbeddingProvider] | None = None,
    ) -> None:
        self.configured = configured
        self.semantic_factory = (
            semantic_factory or SentenceTransformerEmbeddingProvider
        )

    def resolve(
        self,
        *,
        explicit_provider: str | None = None,
    ) -> EmbeddingResolution:
        requested = explicit_provider or self.configured.embedding_provider
        if requested not in self._allowlist:
            raise ValueError("Embedding provider is not allowlisted.")
        if requested == "hashing":
            return EmbeddingResolution(HashingEmbeddingProvider(), requested)

        try:
            if self.configured.hf_model_cache_dir is None:
                raise RuntimeError("Semantic model cache is not configured.")
            provider = self.semantic_factory(
                cache_dir=self.configured.hf_model_cache_dir,
                batch_size=self.configured.embedding_batch_size,
            )
            ensure_available = getattr(provider, "ensure_available", None)
            if ensure_available is not None:
                ensure_available()
            return EmbeddingResolution(provider, requested)
        except Exception as error:
            if explicit_provider is not None:
                raise RuntimeError(
                    "Requested semantic embedding provider is unavailable."
                ) from error
            return EmbeddingResolution(
                HashingEmbeddingProvider(),
                requested,
                fallback_category="model_unavailable",
            )
