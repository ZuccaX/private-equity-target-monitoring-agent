from app.integrations.news.base import RawNewsItem
from app.integrations.news.config import NewsSourceConfig
from app.models.company import Company
from app.services.news_company_matcher import NewsCompanyMatcher


def _company(
    company_id: int,
    name: str,
    domain: str,
    *,
    aliases: list[str] | None = None,
) -> Company:
    company = Company(
        id=company_id,
        name=name,
        domain=domain,
        sector="Software",
        country="France",
        extra_data={"aliases": aliases or []},
    )
    return company


def test_direct_source_binding_cannot_be_overridden() -> None:
    asteria = _company(1, "Asteria HealthCloud", "asteria.example")
    boreal = _company(2, "Boreal Data Systems", "boreal.example")
    source = NewsSourceConfig(
        source_id="direct",
        adapter="mock",
        fixture_path="items.json",
        company_domain="asteria.example",
    )

    result = NewsCompanyMatcher().match(
        RawNewsItem(
            source_item_id="1",
            title="Boreal announced an update",
            company_domain="boreal.example",
        ),
        source,
        [asteria, boreal],
    )

    assert result.company_id == 1
    assert result.method == "source_binding"


def test_aggregate_matches_name_domain_and_alias() -> None:
    company = _company(
        1,
        "Asteria HealthCloud",
        "asteria.example",
        aliases=["Asteria HC"],
    )
    source = NewsSourceConfig(
        source_id="aggregate", adapter="mock", fixture_path="items.json"
    )
    matcher = NewsCompanyMatcher()

    assert matcher.match(
        RawNewsItem(source_item_id="1", title="Asteria HealthCloud expands"),
        source,
        [company],
    ).company_id == 1
    assert matcher.match(
        RawNewsItem(source_item_id="2", title="Update from asteria.example"),
        source,
        [company],
    ).company_id == 1
    assert matcher.match(
        RawNewsItem(source_item_id="3", title="Asteria HC expands"),
        source,
        [company],
    ).company_id == 1


def test_ambiguous_or_boundary_match_is_rejected() -> None:
    source = NewsSourceConfig(
        source_id="aggregate", adapter="mock", fixture_path="items.json"
    )
    companies = [
        _company(1, "North Star", "north.example", aliases=["Nova"]),
        _company(2, "South Star", "south.example", aliases=["Nova"]),
    ]
    matcher = NewsCompanyMatcher()

    assert matcher.match(
        RawNewsItem(source_item_id="1", title="Nova expands"),
        source,
        companies,
    ).accepted is False
    assert matcher.match(
        RawNewsItem(source_item_id="2", title="Innovation update"),
        source,
        companies,
    ).accepted is False
