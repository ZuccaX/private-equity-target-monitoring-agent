from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class EmbeddingIdentity:
    provider: str
    model: str
    version: str
    dimension: int


class EmbeddingProvider(Protocol):
    identity: EmbeddingIdentity

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


def validate_embedding_batch(
    vectors: Sequence[Sequence[float]],
    *,
    expected_rows: int,
    dimension: int,
) -> list[list[float]]:
    if len(vectors) != expected_rows:
        raise ValueError(
            f"Embedding row count {len(vectors)} did not match {expected_rows}."
        )

    validated: list[list[float]] = []
    for vector in vectors:
        values = [float(value) for value in vector]
        if len(values) != dimension:
            raise ValueError(
                f"Embedding dimension {len(values)} did not match {dimension}."
            )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Embedding values must all be finite.")
        validated.append(values)
    return validated
