from sqlalchemy.orm import Session

from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentRead, DocumentSummaryRead


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.document_repository = DocumentRepository(db)

    def list_documents(
        self,
        company_id: int | None = None,
    ) -> list[DocumentSummaryRead]:
        if company_id is None:
            documents = self.document_repository.list_all()
        else:
            documents = self.document_repository.list_by_company_id(
                company_id
            )

        return [
            DocumentSummaryRead.model_validate(document)
            for document in documents
        ]

    def get_document(
        self,
        document_id: int,
    ) -> DocumentRead:
        document = self.document_repository.get_by_id(document_id)

        if document is None:
            raise ValueError(
                f"Document not found: {document_id}"
            )

        return DocumentRead.model_validate(document)