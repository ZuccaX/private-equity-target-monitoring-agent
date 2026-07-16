from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embeddings.base import EmbeddingIdentity


class DocumentChunkRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_document_id(
        self,
        document_id: int,
    ) -> list[DocumentChunk]:
        return (
            self.db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == document_id
            )
            .order_by(
                DocumentChunk.chunk_index.asc()
            )
            .all()
        )

    def list_by_company_id(
        self,
        company_id: int,
    ) -> list[DocumentChunk]:
        return (
            self.db.query(DocumentChunk)
            .filter(
                DocumentChunk.company_id == company_id
            )
            .order_by(
                DocumentChunk.document_id.asc(),
                DocumentChunk.chunk_index.asc(),
            )
            .all()
        )

    def delete_by_document_id(
        self,
        document_id: int,
    ) -> int:
        deleted_count = (
            self.db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == document_id
            )
            .delete(
                synchronize_session=False
            )
        )

        return int(deleted_count)

    def delete_exact_cohort(
        self, document_id: int, identity: EmbeddingIdentity
    ) -> int:
        return int(
            self.db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.embedding_provider == identity.provider,
                DocumentChunk.embedding_model == identity.model,
                DocumentChunk.embedding_model_version == identity.version,
                DocumentChunk.embedding_dimension == identity.dimension,
            )
            .delete(synchronize_session=False)
        )

    def delete_stale_sources(
        self,
        document_id: int,
        *,
        source_content_hash: str,
        source_file_version: str,
    ) -> int:
        return int(
            self.db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == document_id,
                (
                    (DocumentChunk.source_content_hash != source_content_hash)
                    | (DocumentChunk.source_file_version != source_file_version)
                ),
            )
            .delete(synchronize_session=False)
        )

    def create(
        self,
        document_chunk: DocumentChunk,
    ) -> DocumentChunk:
        self.db.add(document_chunk)
        self.db.flush()

        return document_chunk

    def search_similar(
        self,
        query_embedding: list[float],
        top_k: int,
        identity: EmbeddingIdentity,
        company_id: int | None = None,
        document_types: list[str] | None = None,
        minimum_similarity: float | None = None,
    ) -> list[
        tuple[
            DocumentChunk,
            Document,
            float,
        ]
    ]:
        distance_expression = (
            DocumentChunk.embedding.cosine_distance(
                query_embedding
            )
        )
        # pgvector applies filters after approximate HNSW candidate selection,
        # which can produce incomplete company-scoped results. Any filtered
        # retrieval therefore uses an equivalent expression that forces exact
        # ordering; only the unfiltered global debug search may use ANN.
        filtered_search = (
            company_id is not None
            or bool(document_types)
            or minimum_similarity is not None
        )
        order_expression = (
            distance_expression + 0.0
            if filtered_search
            else distance_expression
        )

        query = (
            self.db.query(
                DocumentChunk,
                Document,
                distance_expression.label("distance"),
            )
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .filter(
                Document.deleted_at.is_(None),
                DocumentChunk.embedding_provider == identity.provider,
                DocumentChunk.embedding_model == identity.model,
                DocumentChunk.embedding_model_version == identity.version,
                DocumentChunk.embedding_dimension == identity.dimension,
                DocumentChunk.source_content_hash == Document.content_hash,
                DocumentChunk.source_file_version == Document.file_version,
            )
        )

        if company_id is not None:
            query = query.filter(
                DocumentChunk.company_id == company_id
            )

        if document_types:
            query = query.filter(Document.document_type.in_(document_types))
        if minimum_similarity is not None:
            query = query.filter(distance_expression <= 1.0 - minimum_similarity)

        rows = (
            query.order_by(
                order_expression.asc(),
                DocumentChunk.id.asc(),
            )
            .limit(top_k)
            .all()
        )

        return [
            (
                document_chunk,
                document,
                float(distance),
            )
            for (
                document_chunk,
                document,
                distance,
            ) in rows
        ]
