from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class EvaluationObservation:
    case_id: str
    expected_documents: frozenset[str]
    forbidden_documents: frozenset[str]
    ranked_documents: tuple[str, ...]
    empty: bool
    fallback_used: bool
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalMetrics:
    recall_at_k: float
    mean_reciprocal_rank: float
    leakage_count: int
    irrelevant_inclusion_count: int
    empty_count: int
    fallback_count: int
    warning_count: int


class RetrievalEvaluationService:
    def calculate(
        self, observations: Sequence[EvaluationObservation]
    ) -> RetrievalMetrics:
        expected_cases = [item for item in observations if item.expected_documents]
        recalled = 0
        reciprocal_rank_total = 0.0
        leakage = 0
        for item in observations:
            ranked = list(item.ranked_documents)
            if item.expected_documents:
                ranks = [
                    ranked.index(document) + 1
                    for document in item.expected_documents
                    if document in ranked
                ]
                if ranks:
                    recalled += 1
                    reciprocal_rank_total += 1.0 / min(ranks)
            leakage += sum(
                1 for document in ranked if document in item.forbidden_documents
            )
        denominator = len(expected_cases) or 1
        return RetrievalMetrics(
            recall_at_k=recalled / denominator,
            mean_reciprocal_rank=reciprocal_rank_total / denominator,
            leakage_count=leakage,
            irrelevant_inclusion_count=leakage,
            empty_count=sum(item.empty for item in observations),
            fallback_count=sum(item.fallback_used for item in observations),
            warning_count=sum(len(item.warnings) for item in observations),
        )
