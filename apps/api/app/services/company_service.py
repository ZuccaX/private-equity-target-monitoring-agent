from sqlalchemy.orm import Session

from app.repositories.company_repository import CompanyRepository
from app.schemas.company import CompanyCreate, CompanyRead


class CompanyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.company_repository = CompanyRepository(db)

    def list_companies(self) -> list[CompanyRead]:
        companies = self.company_repository.list_active()

        return [
            CompanyRead.model_validate(company)
            for company in companies
        ]

    def get_company(self, company_id: int) -> CompanyRead:
        company = self.company_repository.get_by_id(company_id)

        if company is None:
            raise ValueError(f"Company not found: {company_id}")

        return CompanyRead.model_validate(company)

    def create_company(self, request: CompanyCreate) -> CompanyRead:
        if request.name.strip() == "":
            raise ValueError("Company name is required.")

        if request.sector.strip() == "":
            raise ValueError("Company sector is required.")

        if request.domain is not None:
            existing_company = self.company_repository.get_by_domain(
                request.domain
            )

            if existing_company is not None:
                raise ValueError(
                    f"Company domain already exists: {request.domain}"
                )

        try:
            company = self.company_repository.create(request)
            self.db.commit()
            self.db.refresh(company)

            return CompanyRead.model_validate(company)

        except Exception:
            self.db.rollback()
            raise