from sqlalchemy.orm import Session

from app.models.crm_interaction import CRMInteraction


class CRMInteractionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[CRMInteraction]:
        return (
            self.db.query(CRMInteraction)
            .order_by(CRMInteraction.occurred_at.desc())
            .all()
        )

    def list_by_company_id(
        self,
        company_id: int,
    ) -> list[CRMInteraction]:
        return (
            self.db.query(CRMInteraction)
            .filter(CRMInteraction.company_id == company_id)
            .order_by(CRMInteraction.occurred_at.desc())
            .all()
        )

    def get_by_external_id(
        self,
        external_id: str,
    ) -> CRMInteraction | None:
        return (
            self.db.query(CRMInteraction)
            .filter(CRMInteraction.external_id == external_id)
            .first()
        )

    def create(
        self,
        interaction: CRMInteraction,
    ) -> CRMInteraction:
        self.db.add(interaction)
        self.db.flush()

        return interaction