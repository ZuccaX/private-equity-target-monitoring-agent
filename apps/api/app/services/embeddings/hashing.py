from __future__ import annotations

import hashlib
import math
import re
from typing import Sequence

from app.services.embeddings.base import (
    EmbeddingIdentity,
    validate_embedding_batch,
)


class HashingEmbeddingProvider:
    identity = EmbeddingIdentity(
        provider="hashing",
        model="local-hashing-384-v1",
        version="1",
        dimension=384,
    )

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = [self._embed(text) for text in texts]
        return validate_embedding_batch(
            vectors,
            expected_rows=len(texts),
            dimension=self.identity.dimension,
        )

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.identity.dimension)]
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.identity.dimension
            vector[index] += 1.0 if digest[4] % 2 == 0 else -1.0

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]
