from sqlalchemy.orm import Session

from app.repositories.investment_mandate_repository import InvestmentMandateRepository
from app.schemas.mandate import (
    InvestmentMandateBase,
    InvestmentMandateCreate,
    InvestmentMandateRead,
    InvestmentMandateUpdate,
)


class InvestmentMandateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = InvestmentMandateRepository(db)

    def list_mandates(
        self,
        *,
        active_only: bool,
        offset: int,
        limit: int,
    ) -> list[InvestmentMandateRead]:
        return [
            InvestmentMandateRead.model_validate(mandate)
            for mandate in self.repository.list_all(
                active_only=active_only,
                offset=offset,
                limit=limit,
            )
        ]

    def get_mandate(self, mandate_id: int) -> InvestmentMandateRead:
        mandate = self.repository.get_by_id(mandate_id)
        if mandate is None:
            raise ValueError(f"Investment mandate not found: {mandate_id}")
        return InvestmentMandateRead.model_validate(mandate)

    def create_mandate(
        self, request: InvestmentMandateCreate
    ) -> InvestmentMandateRead:
        if self.repository.get_by_name(request.name) is not None:
            raise ValueError(f"Investment mandate name already exists: {request.name}")
        try:
            mandate = self.repository.create(request)
            self.db.commit()
            self.db.refresh(mandate)
            return InvestmentMandateRead.model_validate(mandate)
        except Exception:
            self.db.rollback()
            raise

    def update_mandate(
        self,
        mandate_id: int,
        request: InvestmentMandateUpdate,
    ) -> InvestmentMandateRead:
        mandate = self.repository.get_by_id(mandate_id)
        if mandate is None:
            raise ValueError(f"Investment mandate not found: {mandate_id}")

        changes = request.model_dump(exclude_unset=True)
        current = InvestmentMandateRead.model_validate(mandate).model_dump(
            exclude={"id", "created_at", "updated_at"}
        )
        validated = InvestmentMandateBase.model_validate({**current, **changes})

        if "name" in changes:
            duplicate = self.repository.get_by_name(validated.name)
            if duplicate is not None and duplicate.id != mandate_id:
                raise ValueError(
                    f"Investment mandate name already exists: {validated.name}"
                )

        try:
            for field, value in validated.model_dump().items():
                if field in changes:
                    setattr(mandate, field, value)
            self.db.commit()
            self.db.refresh(mandate)
            return InvestmentMandateRead.model_validate(mandate)
        except Exception:
            self.db.rollback()
            raise
