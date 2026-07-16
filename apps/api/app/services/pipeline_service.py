from sqlalchemy.orm import Session

from app.repositories.company_repository import CompanyRepository
from app.repositories.investment_mandate_repository import InvestmentMandateRepository
from app.schemas.company import CompanyRead
from app.schemas.pipeline import CompanyPipelineUpdate


class PipelineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.company_repository = CompanyRepository(db)
        self.mandate_repository = InvestmentMandateRepository(db)

    def list_pipeline(self) -> list[CompanyRead]:
        return [
            CompanyRead.model_validate(company)
            for company in self.company_repository.list_active()
        ]

    def update_company_pipeline(
        self,
        company_id: int,
        request: CompanyPipelineUpdate,
    ) -> CompanyRead:
        company = self.company_repository.get_by_id(company_id)
        if company is None:
            raise ValueError(f"Company not found: {company_id}")

        changes = request.model_dump(exclude_unset=True)
        mandate_id = changes.get("mandate_id")
        if mandate_id is not None and self.mandate_repository.get_by_id(
            mandate_id
        ) is None:
            raise ValueError(f"Investment mandate not found: {mandate_id}")

        if changes.get("pipeline_stage") == "passed" and not (
            changes.get("pass_reason") or company.pass_reason
        ):
            raise ValueError("pass_reason is required when pipeline_stage is passed")

        try:
            for field, value in changes.items():
                setattr(company, field, value)
            self.db.commit()
            self.db.refresh(company)
            return CompanyRead.model_validate(company)
        except Exception:
            self.db.rollback()
            raise
