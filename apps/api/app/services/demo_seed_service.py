from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.content_identity import canonical_content_hash
from app.models.agent_run import AgentRun
from app.models.approval import Approval
from app.models.company import Company
from app.models.contact import Contact
from app.models.crm_interaction import CRMInteraction
from app.models.document import Document
from app.models.email_draft import EmailDraft
from app.models.feedback import Feedback
from app.models.investment_mandate import InvestmentMandate
from app.models.news_article import NewsArticle
from app.models.priority_score import PriorityScore
from app.models.trigger import Trigger


SEED_OWNER = "milestone2-demo-v1"


class DemoSeedService:
    def __init__(self, db: Session, seed_dir: Path) -> None:
        self.db = db
        self.seed_dir = seed_dir

    def _load(self, name: str) -> list[dict[str, Any]]:
        value = json.loads((self.seed_dir / name).read_text(encoding="utf-8"))
        if not isinstance(value, list):
            raise ValueError(f"Seed file must contain a list: {name}")
        return value

    @staticmethod
    def _assert_owned(metadata: dict[str, Any] | None, natural_key: str) -> None:
        if (metadata or {}).get("seed_owner") != SEED_OWNER:
            raise ValueError(
                f"Refusing to overwrite unowned row with natural key {natural_key}."
            )

    def seed(self) -> dict[str, int]:
        try:
            with self.db.no_autoflush:
                self._seed_mandates()
                self._seed_companies()
                self._seed_contacts()
                self._seed_interactions()
                self._seed_documents()
                self._seed_news()
                self._seed_triggers()
                self._seed_workflows()
                self._seed_approvals()
                self._seed_feedback()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return {
            "companies": self.db.query(Company).filter(
                Company.extra_data["seed_owner"].astext == SEED_OWNER
            ).count(),
            "documents": self.db.query(Document).filter(
                Document.extra_data["seed_owner"].astext == SEED_OWNER
            ).count(),
            "news_articles": self.db.query(NewsArticle).filter(
                NewsArticle.raw_payload["seed_owner"].astext == SEED_OWNER
            ).count(),
        }

    def _seed_mandates(self) -> None:
        for item in self._load("mandates.json"):
            row = self.db.query(InvestmentMandate).filter_by(name=item["name"]).first()
            if row is not None:
                self._assert_owned(row.extra_data, item["name"])
            else:
                row = InvestmentMandate(name=item["name"])
                self.db.add(row)
            row.description = item.get("description")
            row.target_sectors = item.get("target_sectors", [])
            row.excluded_sectors = item.get("excluded_sectors", [])
            row.target_countries = item.get("target_countries", [])
            row.preferred_business_models = item.get("preferred_business_models", [])
            row.is_active = item.get("is_active", True)
            row.extra_data = {
                "seed_owner": SEED_OWNER,
                "seed_id": item["seed_id"],
            }
        self.db.flush()

    def _mandate_by_seed_id(self, seed_id: str) -> InvestmentMandate:
        return self.db.query(InvestmentMandate).filter(
            InvestmentMandate.extra_data["seed_id"].astext == seed_id
        ).one()

    def _seed_companies(self) -> None:
        for item in self._load("companies.json"):
            row = self.db.query(Company).filter_by(domain=item["domain"]).first()
            if row is not None:
                self._assert_owned(row.extra_data, item["domain"])
            else:
                row = Company(domain=item["domain"])
                self.db.add(row)
            row.name = item["name"]
            row.sector = item["sector"]
            row.country = item["country"]
            row.status = item.get("status", "active")
            row.pipeline_stage = item.get("pipeline_stage", "sourced")
            row.description = item.get("description")
            row.source = "milestone2_seed"
            row.source_channel = "seed"
            row.mandate_id = self._mandate_by_seed_id(item["mandate_seed_id"]).id
            row.extra_data = {
                "seed_owner": SEED_OWNER,
                "seed_id": item["seed_id"],
            }
        self.db.flush()

    def _company(self, domain: str) -> Company:
        return self.db.query(Company).filter_by(domain=domain).one()

    def _seed_contacts(self) -> None:
        for item in self._load("contacts.json"):
            row = self.db.query(Contact).filter_by(
                external_id=item["external_id"]
            ).first()
            if row is not None and row.source != "milestone2_seed":
                raise ValueError("Refusing to overwrite unowned contact.")
            if row is None:
                row = Contact(external_id=item["external_id"])
                self.db.add(row)
            row.company_id = self._company(item["company_domain"]).id
            row.full_name = item["full_name"]
            row.job_title = item.get("job_title")
            row.email = item.get("email")
            row.relationship_strength = item.get("relationship_strength", 0)
            row.source = "milestone2_seed"
        self.db.flush()

    def _seed_interactions(self) -> None:
        for item in self._load("crm_interactions.json"):
            row = self.db.query(CRMInteraction).filter_by(
                external_id=item["external_id"]
            ).first()
            if row is not None:
                self._assert_owned(row.raw_payload, item["external_id"])
            else:
                row = CRMInteraction(external_id=item["external_id"])
                self.db.add(row)
            row.company_id = self._company(item["company_domain"]).id
            row.contact_id = self.db.query(Contact).filter_by(
                external_id=item["contact_external_id"]
            ).one().id
            row.interaction_type = item["interaction_type"]
            row.direction = item["direction"]
            row.summary = item["summary"]
            row.occurred_at = datetime.fromisoformat(item["occurred_at"])
            row.source = "milestone2_seed"
            row.raw_payload = {"seed_owner": SEED_OWNER}

    def _seed_documents(self) -> None:
        for item in self._load("documents.json"):
            row = self.db.query(Document).filter_by(
                external_id=item["external_id"]
            ).first()
            if row is not None:
                self._assert_owned(row.extra_data, item["external_id"])
            else:
                row = Document(external_id=item["external_id"])
                self.db.add(row)
            row.company_id = self._company(item["company_domain"]).id
            row.title = item["title"]
            row.file_name = item["file_name"]
            row.document_type = item["document_type"]
            row.source_system = item["source_system"]
            row.source_path = item.get("source_path")
            row.content_text = item["content_text"]
            row.content_hash = canonical_content_hash(item["content_text"])
            row.file_version = item["file_version"]
            row.sync_status = "synced"
            row.extra_data = {
                "seed_owner": SEED_OWNER,
                "irrelevant": item.get("irrelevant", False),
            }

    def _seed_news(self) -> None:
        seen: set[str] = set()
        for item in self._load("news_articles.json"):
            external_id = item["external_id"]
            if external_id in seen:
                continue
            seen.add(external_id)
            row = self.db.query(NewsArticle).filter_by(external_id=external_id).first()
            if row is not None:
                self._assert_owned(row.raw_payload, external_id)
            else:
                row = NewsArticle(external_id=external_id)
                self.db.add(row)
            row.company_id = self._company(item["company_domain"]).id
            row.title = item["title"]
            row.summary = item.get("summary")
            row.url = item.get("url")
            row.canonical_url = item.get("url")
            row.source = item.get("source", "mock_news")
            row.content_hash = hashlib.sha256(
                f"{row.title}\n{row.summary or ''}".encode("utf-8")
            ).hexdigest()
            row.raw_payload = {"seed_owner": SEED_OWNER}

    def _seed_triggers(self) -> None:
        for item in self._load("triggers.json"):
            row = self.db.query(Trigger).filter_by(
                deduplication_key=item["seed_id"]
            ).first()
            if row is None:
                row = Trigger(deduplication_key=item["seed_id"])
                self.db.add(row)
            row.company_id = self._company(item["company_domain"]).id
            row.trigger_type = item["trigger_type"]
            row.title = item["title"]
            row.confidence_score = item["confidence_score"]
            row.is_negative = item["is_negative"]
            row.evidence_refs = [{"seed_owner": SEED_OWNER}]
            row.extraction_method = "seed"

    def _seed_workflows(self) -> None:
        for item in self._load("demo_workflows.json"):
            row = self.db.query(AgentRun).filter(
                AgentRun.input_snapshot["seed_id"].astext == item["seed_id"]
            ).first()
            company = self._company(item["company_domain"])
            if row is None:
                row = AgentRun(company_id=company.id)
                self.db.add(row)
            row.company_id = company.id
            row.run_type = "full_workflow"
            row.status = item["status"]
            row.workflow_version = "m2-demo-v1"
            row.model_name = item["model_name"]
            row.prompt_version = "m2-demo-v1"
            row.input_snapshot = {
                "seed_owner": SEED_OWNER,
                "seed_id": item["seed_id"],
                "fallback_reason": item["fallback_reason"],
            }
            row.output_summary = "Deterministic seeded workflow."
            row.started_at = row.started_at or datetime.now(UTC)
            row.completed_at = row.completed_at or datetime.now(UTC)
            self.db.flush()
            score = self.db.query(PriorityScore).filter_by(agent_run_id=row.id).first()
            if score is None:
                score = PriorityScore(agent_run_id=row.id, company_id=company.id)
                self.db.add(score)
            score.overall_score = item["overall_score"]
            score.score_version = "m2-demo-v1"
            score.sector_fit_score = item["overall_score"]
            score.trigger_score = item["overall_score"]
            score.relationship_score = item["overall_score"]
            score.timing_score = item["overall_score"]
            score.risk_score = 100 - item["overall_score"]
            score.reasons = ["Deterministic demo score"]
            score.evidence_refs = []
            draft = self.db.query(EmailDraft).filter_by(agent_run_id=row.id).first()
            if draft is None:
                draft = EmailDraft(agent_run_id=row.id, company_id=company.id)
                self.db.add(draft)
            draft.subject = f"Introduction to {company.name}"
            draft.body = "Seeded draft; never send automatically."
            draft.status = item["draft_status"]
            draft.generated_by = "template"
            draft.evidence_refs = []
        self.db.flush()

    def _run(self, seed_id: str) -> AgentRun:
        return self.db.query(AgentRun).filter(
            AgentRun.input_snapshot["seed_id"].astext == seed_id
        ).one()

    def _seed_approvals(self) -> None:
        for item in self._load("approvals.json"):
            if item["decision"] == "pending":
                raise ValueError("Pending is a draft state, not an approval decision.")
            draft = self.db.query(EmailDraft).filter_by(
                agent_run_id=self._run(item["run_seed_id"]).id
            ).one()
            row = self.db.query(Approval).filter_by(
                email_draft_id=draft.id, decision=item["decision"]
            ).first()
            if row is None:
                row = Approval(email_draft_id=draft.id, decision=item["decision"])
                self.db.add(row)
            row.comment = f"[{SEED_OWNER}:{item['seed_id']}] {item['comment']}"
            row.reviewer_name = "Demo IC"
            row.reviewer_role = "Investment Committee"

    def _seed_feedback(self) -> None:
        for item in self._load("feedback.json"):
            row = self.db.query(Feedback).filter(
                Feedback.extra_data["seed_id"].astext == item["seed_id"]
            ).first()
            if row is None:
                row = Feedback(feedback_type=item["feedback_type"])
                self.db.add(row)
            row.company_id = self._company(item["company_domain"]).id
            row.agent_run_id = (
                self._run(item["run_seed_id"]).id
                if item.get("run_seed_id")
                else None
            )
            row.feedback_type = item["feedback_type"]
            row.rating = item["rating"]
            row.is_helpful = item["is_helpful"]
            row.comment = item["comment"]
            row.submitted_by = "demo-reviewer"
            row.extra_data = {"seed_owner": SEED_OWNER, "seed_id": item["seed_id"]}
