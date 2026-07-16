from sqlalchemy.orm import Session

from app.models.investment_mandate import InvestmentMandate
from app.schemas.mandate import InvestmentMandateCreate


class InvestmentMandateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(
        self,
        *,
        active_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[InvestmentMandate]:
        query = self.db.query(InvestmentMandate)
        if active_only:
            query = query.filter(InvestmentMandate.is_active.is_(True))
        return query.order_by(InvestmentMandate.name.asc()).offset(offset).limit(limit).all()

    def get_by_id(self, mandate_id: int) -> InvestmentMandate | None:
        return self.db.query(InvestmentMandate).filter(
            InvestmentMandate.id == mandate_id
        ).first()

    def get_by_name(self, name: str) -> InvestmentMandate | None:
        return self.db.query(InvestmentMandate).filter(
            InvestmentMandate.name == name
        ).first()

    def create(self, request: InvestmentMandateCreate) -> InvestmentMandate:
        mandate = InvestmentMandate(**request.model_dump(), extra_data={})
        self.db.add(mandate)
        self.db.flush()
        return mandate
