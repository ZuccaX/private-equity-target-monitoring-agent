from sqlalchemy.orm import Session

from app.models.company import Company


def _seed_companies(db: Session) -> None:
    for name, domain in (
        ("Asteria", "asteria.example"),
        ("Esker", "esker.example"),
        ("Fjord", "fjord.example"),
    ):
        db.add(
            Company(
                name=name,
                domain=domain,
                sector="Software",
                country="France",
                extra_data={},
            )
        )
    db.commit()


def test_news_sync_and_trigger_extract_actions_are_typed(
    api_client,
    db_session: Session,
) -> None:
    _seed_companies(db_session)
    sync = api_client.post(
        "/api/news-articles/sync",
        json={"source_ids": ["demo_mock"], "extract_triggers": False},
    )
    assert sync.status_code == 200
    assert sync.json()["created"] == 3

    extract = api_client.post(
        "/api/triggers/extract",
        json={"company_id": 1, "status": "pending"},
    )
    assert extract.status_code == 200
    assert extract.json()["selected"] >= 1

    forbidden = api_client.post(
        "/api/news-articles/sync",
        json={"source_ids": ["demo_mock"], "url": "https://evil.test"},
    )
    assert forbidden.status_code == 422


def test_unknown_source_and_openapi_contract(api_client) -> None:
    response = api_client.post(
        "/api/news-articles/sync", json={"source_ids": ["unknown"]}
    )
    assert response.status_code == 422
    schema = api_client.get("/openapi.json").json()
    assert "post" in schema["paths"]["/api/news-articles/sync"]
    assert "post" in schema["paths"]["/api/triggers/extract"]
