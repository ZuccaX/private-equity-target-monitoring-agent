from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.core.content_identity import LEGACY_FILE_VERSION, canonical_content_hash
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.repositories.document_repository import (
    DocumentRepository,
)
from app.services.chunking_service import (
    ChunkingService,
)
from app.services.embedding_service import (
    EmbeddingService,
)
from app.services.embeddings.base import validate_embedding_batch


@dataclass(frozen=True)
class DocumentIndexingSummary:
    documents_indexed: int
    documents_skipped: int
    chunks_created: int
    indexed_identities: tuple[str, ...] = ()
    provider_failures: tuple[str, ...] = ()


class DocumentIndexingService:
    def __init__(
        self,
        db: Session,
        chunking_service: ChunkingService | None = None,
        embedding_service: EmbeddingService | None = None,
        embedding_services: Sequence[EmbeddingService] | None = None,
    ) -> None:
        self.db = db

        self.document_repository = (
            DocumentRepository(db)
        )

        self.document_chunk_repository = (
            DocumentChunkRepository(db)
        )

        self.chunking_service = (
            chunking_service
            or ChunkingService()
        )

        selected = embedding_service or EmbeddingService()
        self.embedding_services = tuple(embedding_services or (selected,))

    def index_all_documents(
        self,
    ) -> DocumentIndexingSummary:
        documents = (
            self.document_repository.list_all()
        )

        documents_indexed = 0
        documents_skipped = 0
        chunks_created = 0
        indexed_identities: set[str] = set()
        provider_failures: list[str] = []

        try:
            for document in documents:
                content_text = (
                    document.content_text
                    or ""
                ).strip()

                if content_text == "":
                    documents_skipped += 1
                    continue

                source_content_hash = canonical_content_hash(document.content_text)
                source_file_version = document.file_version or LEGACY_FILE_VERSION
                document.content_hash = source_content_hash
                document.file_version = source_file_version
                self.document_chunk_repository.delete_stale_sources(
                    document.id,
                    source_content_hash=source_content_hash,
                    source_file_version=source_file_version,
                )

                chunks = (
                    self.chunking_service
                    .split_text(content_text)
                )

                document_succeeded = False
                last_provider_error: Exception | None = None
                texts = [chunk.chunk_text for chunk in chunks]
                for embedding_service in self.embedding_services:
                    identity = embedding_service.identity
                    try:
                        vectors = validate_embedding_batch(
                            embedding_service.embed_documents(texts),
                            expected_rows=len(chunks),
                            dimension=identity.dimension,
                        )
                        with self.db.begin_nested():
                            self.document_chunk_repository.delete_exact_cohort(
                                document.id, identity
                            )
                            for chunk, embedding in zip(chunks, vectors, strict=True):
                                self.document_chunk_repository.create(
                                    DocumentChunk(
                                        document_id=document.id,
                                        company_id=document.company_id,
                                        chunk_index=chunk.chunk_index,
                                        chunk_text=chunk.chunk_text,
                                        token_count=chunk.token_count,
                                        embedding=embedding,
                                        embedding_provider=identity.provider,
                                        embedding_model=identity.model,
                                        embedding_model_version=identity.version,
                                        embedding_dimension=identity.dimension,
                                        source_content_hash=source_content_hash,
                                        source_file_version=source_file_version,
                                        extra_data={
                                            "document_title": document.title,
                                            "document_type": document.document_type,
                                            "source_system": document.source_system,
                                        },
                                    )
                                )
                        chunks_created += len(chunks)
                        document_succeeded = True
                        indexed_identities.add(
                            f"{identity.provider}:{identity.model}@{identity.version}"
                        )
                    except Exception as error:
                        last_provider_error = error
                        provider_failures.append(
                            f"{identity.provider}:{type(error).__name__}"
                        )

                if document_succeeded:
                    document.indexed_at = datetime.now(UTC)
                    documents_indexed += 1
                else:
                    raise RuntimeError(
                        f"All embedding providers failed for document {document.id}."
                    ) from last_provider_error

            self.db.commit()

            return DocumentIndexingSummary(
                documents_indexed=(
                    documents_indexed
                ),
                documents_skipped=(
                    documents_skipped
                ),
                chunks_created=chunks_created,
                indexed_identities=tuple(sorted(indexed_identities)),
                provider_failures=tuple(provider_failures),
            )

        except Exception:
            self.db.rollback()
            raise
