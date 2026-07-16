from sqlalchemy.orm import Session

from app.repositories.contact_repository import ContactRepository
from app.repositories.crm_interaction_repository import (
    CRMInteractionRepository,
)
from app.schemas.crm import ContactRead, CRMInteractionRead


class CRMService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.contact_repository = ContactRepository(db)
        self.interaction_repository = CRMInteractionRepository(db)

    def list_contacts(
        self,
        company_id: int | None = None,
    ) -> list[ContactRead]:
        if company_id is None:
            contacts = self.contact_repository.list_all()
        else:
            contacts = self.contact_repository.list_by_company_id(
                company_id
            )

        return [
            ContactRead.model_validate(contact)
            for contact in contacts
        ]

    def list_interactions(
        self,
        company_id: int | None = None,
    ) -> list[CRMInteractionRead]:
        if company_id is None:
            interactions = self.interaction_repository.list_all()
        else:
            interactions = (
                self.interaction_repository.list_by_company_id(
                    company_id
                )
            )

        return [
            CRMInteractionRead.model_validate(interaction)
            for interaction in interactions
        ]