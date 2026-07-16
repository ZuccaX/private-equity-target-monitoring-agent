from sqlalchemy.orm import Session

from app.models.company import Company
from app.schemas.company import CompanyCreate


class CompanyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active(self) -> list[Company]:
        return (
            self.db.query(Company)
            .filter(Company.deleted_at.is_(None))
            .order_by(Company.id.asc())
            .all()
        )

    def get_by_id(self, company_id: int) -> Company | None:
        return (
            self.db.query(Company)
            .filter(
                Company.id == company_id,
                Company.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_domain(self, domain: str) -> Company | None:
        return (
            self.db.query(Company)
            .filter(
                Company.domain == domain,
                Company.deleted_at.is_(None),
            )
            .first()
        )

    def list_matchable(self) -> list[Company]:
        return self.list_active()

    def create(self, request: CompanyCreate) -> Company:
        company = Company(
            name=request.name,
            website=request.website,
            domain=request.domain,
            sector=request.sector,
            country=request.country,
            description=request.description,
            mandate_id=request.mandate_id,
            status="new",
            pipeline_stage="sourced",
            source_channel="manual",
            source="manual",
            extra_data={},
        )

        self.db.add(company)
        self.db.flush()

        return company
