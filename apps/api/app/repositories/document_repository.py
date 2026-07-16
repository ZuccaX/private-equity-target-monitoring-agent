from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Document]:
        return (
            self.db.query(Document)
            .filter(Document.deleted_at.is_(None))
            .order_by(Document.uploaded_at.desc().nullslast())
            .all()
        )

    def list_by_company_id(
        self,
        company_id: int,
    ) -> list[Document]:
        return (
            self.db.query(Document)
            .filter(
                Document.company_id == company_id,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.uploaded_at.desc().nullslast())
            .all()
        )

    def get_by_id(
        self,
        document_id: int,
    ) -> Document | None:
        return (
            self.db.query(Document)
            .filter(
                Document.id == document_id,
                Document.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_external_id(
        self,
        external_id: str,
    ) -> Document | None:
        return (
            self.db.query(Document)
            .filter(
                Document.external_id == external_id,
                Document.deleted_at.is_(None),
            )
            .first()
        )

    def create(
        self,
        document: Document,
    ) -> Document:
        self.db.add(document)
        self.db.flush()

        return document