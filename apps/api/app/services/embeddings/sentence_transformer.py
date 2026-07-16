from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from app.services.embeddings.base import (
    EmbeddingIdentity,
    validate_embedding_batch,
)


class SentenceTransformerEmbeddingProvider:
    identity = EmbeddingIdentity(
        provider="sentence_transformer",
        model="sentence-transformers/all-MiniLM-L6-v2",
        version="1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        dimension=384,
    )

    def __init__(self, *, cache_dir: Path, batch_size: int = 32) -> None:
        self.cache_dir = cache_dir
        self.batch_size = batch_size
        self._model: Any | None = None

    def _load_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.identity.model,
                revision=self.identity.version,
                cache_folder=str(self.cache_dir),
                device="cpu",
                local_files_only=True,
            )
        return self._model

    def ensure_available(self) -> None:
        self._load_model()

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        encoded = self._load_model().encode(
            list(texts),
            convert_to_numpy=False,
            normalize_embeddings=True,
            batch_size=self.batch_size,
        )
        return validate_embedding_batch(
            encoded,
            expected_rows=len(texts),
            dimension=self.identity.dimension,
        )

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
