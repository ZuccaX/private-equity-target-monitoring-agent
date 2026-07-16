from types import SimpleNamespace

from app.services.rag_query_service import RAGQueryService


def test_query_combines_company_mandate_geography_and_recent_trigger() -> None:
    query = RAGQueryService().build(
        user_query="Assess fit",
        company=SimpleNamespace(name="Acme", sector="Software", country="France"),
        mandate=SimpleNamespace(
            name="European Growth",
            target_sectors=["Software"],
            target_countries=["France"],
        ),
        triggers=[SimpleNamespace(title="New CFO appointed")],
    )

    assert "Assess fit" in query
    assert "Acme" in query
    assert "European Growth" in query
    assert "New CFO appointed" in query


def test_query_handles_missing_optional_context() -> None:
    query = RAGQueryService().build(
        user_query="question",
        company=SimpleNamespace(name="Acme", sector="Tech", country="UK"),
        mandate=None,
        triggers=[],
    )
    assert query.startswith("question")
