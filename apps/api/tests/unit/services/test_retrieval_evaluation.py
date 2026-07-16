from app.services.retrieval_evaluation_service import (
    EvaluationObservation,
    RetrievalEvaluationService,
)


def test_retrieval_metrics_cover_recall_mrr_leakage_empty_and_fallback() -> None:
    metrics = RetrievalEvaluationService().calculate(
        [
            EvaluationObservation(
                case_id="hit",
                expected_documents=frozenset({"expected"}),
                forbidden_documents=frozenset({"forbidden"}),
                ranked_documents=("other", "expected"),
                empty=False,
                fallback_used=True,
                warnings=("fallback",),
            ),
            EvaluationObservation(
                case_id="leak",
                expected_documents=frozenset({"missed"}),
                forbidden_documents=frozenset({"forbidden"}),
                ranked_documents=("forbidden",),
                empty=False,
                fallback_used=False,
                warnings=(),
            ),
            EvaluationObservation(
                case_id="empty",
                expected_documents=frozenset(),
                forbidden_documents=frozenset(),
                ranked_documents=(),
                empty=True,
                fallback_used=False,
                warnings=(),
            ),
        ]
    )

    assert metrics.recall_at_k == 0.5
    assert metrics.mean_reciprocal_rank == 0.25
    assert metrics.leakage_count == 1
    assert metrics.irrelevant_inclusion_count == 1
    assert metrics.empty_count == 1
    assert metrics.fallback_count == 1
    assert metrics.warning_count == 1
