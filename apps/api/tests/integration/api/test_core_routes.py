from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.agent_run import AgentRun
from app.models.agent_run_step import AgentRunStep
from app.models.company import Company


def test_mandate_pipeline_feedback_and_run_step_contracts(
    api_client: TestClient,
    db_session: Session,
) -> None:
    mandate_response = api_client.post(
        "/api/mandates",
        json={
            "name": "European B2B Software",
            "target_sectors": ["Software", " Software "],
            "target_countries": ["France", "Germany"],
            "revenue_min": 10,
            "revenue_max": 100,
        },
    )
    assert mandate_response.status_code == 201
    mandate = mandate_response.json()
    assert mandate["target_sectors"] == ["Software"]

    company = Company(
        name="Pipeline Company",
        sector="Software",
        country="France",
        status="active",
        extra_data={},
    )
    db_session.add(company)
    db_session.commit()

    pipeline_response = api_client.patch(
        f"/api/pipeline/companies/{company.id}",
        json={
            "mandate_id": mandate["id"],
            "pipeline_stage": "screening",
            "owner": "Deal Team",
            "next_action": "Review retention",
        },
    )
    assert pipeline_response.status_code == 200
    assert pipeline_response.json()["pipeline_stage"] == "screening"

    run = AgentRun(
        company_id=company.id,
        run_type="origination",
        status="completed",
        workflow_version="test",
        input_snapshot={},
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    db_session.add(run)
    db_session.flush()
    db_session.add(
        AgentRunStep(
            agent_run_id=run.id,
            node_name="load_company",
            status="completed",
            extra_data={},
        )
    )
    db_session.commit()

    step_response = api_client.get(f"/api/agent-runs/{run.id}/steps")
    assert step_response.status_code == 200
    assert step_response.json()[0]["node_name"] == "load_company"

    feedback_response = api_client.post(
        "/api/feedback",
        json={
            "agent_run_id": run.id,
            "company_id": company.id,
            "feedback_type": "overall_run",
            "rating": 4,
            "submitted_by": "Reviewer",
        },
    )
    assert feedback_response.status_code == 201
    assert feedback_response.json()["rating"] == 4

    assert api_client.get("/api/mandates?active_only=true").status_code == 200
    assert api_client.get("/api/pipeline").status_code == 200
    assert api_client.get("/api/feedback").status_code == 200
    assert api_client.get("/api/audit").status_code == 200


def test_preserved_get_route_contracts(api_client: TestClient) -> None:
    paths = (
        "/api/companies",
        "/api/agent-runs",
        "/api/drafts",
        "/api/news-articles",
        "/api/triggers",
        "/api/dashboard/summary",
        "/api/crm/contacts",
        "/api/crm/interactions",
        "/api/documents",
    )

    for path in paths:
        response = api_client.get(path)
        assert response.status_code == 200, (path, response.text)


def test_agent_run_persists_steps_and_draft_revision(
    api_client: TestClient,
    db_session: Session,
) -> None:
    company = Company(
        name="Workflow Company",
        sector="Business Services",
        country="France",
        status="active",
        extra_data={},
    )
    db_session.add(company)
    db_session.commit()

    run_response = api_client.post(f"/api/agent-runs/{company.id}")
    assert run_response.status_code == 200, run_response.text
    run_payload = run_response.json()
    run_id = run_payload["agent_run"]["id"]
    draft_id = run_payload["email_draft"]["id"]

    steps_response = api_client.get(f"/api/agent-runs/{run_id}/steps")
    assert steps_response.status_code == 200
    steps = steps_response.json()
    assert [step["node_name"] for step in steps] == [
        "load_context",
        "execute_workflow",
        "persist_results",
    ]
    assert {step["status"] for step in steps} == {"completed"}

    original_subject = run_payload["email_draft"]["subject"]
    update_response = api_client.patch(
        f"/api/drafts/{draft_id}",
        json={
            "subject": "Reviewer edited subject",
            "reviewer_name": "Reviewer",
            "comment": "Tighten the opening",
        },
    )
    assert update_response.status_code == 200

    revisions_response = api_client.get(f"/api/drafts/{draft_id}/revisions")
    assert revisions_response.status_code == 200
    revisions = revisions_response.json()
    assert len(revisions) == 1
    assert revisions[0]["subject"] == original_subject
    assert revisions[0]["editor_name"] == "Reviewer"


def test_openapi_preserves_and_adds_required_paths(api_client: TestClient) -> None:
    paths = api_client.get("/openapi.json").json()["paths"]

    expected_paths = {
        "/api/companies",
        "/api/agent-runs/{company_id}",
        "/api/drafts/{draft_id}",
        "/api/news-articles",
        "/api/triggers",
        "/api/dashboard/summary",
        "/api/crm/contacts",
        "/api/documents",
        "/api/vector/search",
        "/api/rag/retrieve",
        "/api/mandates",
        "/api/pipeline",
        "/api/integrations/health",
        "/api/audit",
        "/api/feedback",
        "/api/agent-runs/{agent_run_id}/steps",
        "/api/drafts/{draft_id}/revisions",
    }
    assert expected_paths <= set(paths)
