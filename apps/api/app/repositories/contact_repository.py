from sqlalchemy.orm import Session

from app.models.contact import Contact


class ContactRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Contact]:
        return (
            self.db.query(Contact)
            .order_by(Contact.relationship_strength.desc())
            .all()
        )

    def list_by_company_id(self, company_id: int) -> list[Contact]:
        return (
            self.db.query(Contact)
            .filter(Contact.company_id == company_id)
            .order_by(Contact.relationship_strength.desc())
            .all()
        )

    def get_by_id(self, contact_id: int) -> Contact | None:
        return (
            self.db.query(Contact)
            .filter(Contact.id == contact_id)
            .first()
        )

    def get_by_external_id(
        self,
        external_id: str,
    ) -> Contact | None:
        return (
            self.db.query(Contact)
            .filter(Contact.external_id == external_id)
            .first()
        )

    def create(self, contact: Contact) -> Contact:
        self.db.add(contact)
        self.db.flush()

        return contact