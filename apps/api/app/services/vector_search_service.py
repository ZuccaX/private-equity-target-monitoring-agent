from sqlalchemy.orm import Session

from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.schemas.vector_search import (
    EmbeddingIdentityRead,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResultRead,
)
from app.services.embedding_service import (
    EmbeddingService,
)
from app.core.config import Settings, settings
from app.services.embeddings.registry import EmbeddingProviderRegistry


class VectorSearchService:
    def __init__(
        self,
        db: Session,
        embedding_service: EmbeddingService | None = None,
        configured: Settings = settings,
    ) -> None:
        self.document_chunk_repository = (
            DocumentChunkRepository(db)
        )

        self.configured = configured
        self.embedding_service = embedding_service

    def search(
        self,
        request: VectorSearchRequest,
    ) -> VectorSearchResponse:
        explicit = any(
            (
                request.embedding_provider,
                request.embedding_model,
                request.embedding_model_version,
            )
        )
        resolution = EmbeddingProviderRegistry(self.configured).resolve(
            explicit_provider=request.embedding_provider if explicit else None
        )
        service = self.embedding_service or EmbeddingService(resolution.provider)
        identity = service.identity
        if request.embedding_model and request.embedding_model != identity.model:
            raise ValueError("Requested embedding model identity is unavailable.")
        if (
            request.embedding_model_version
            and request.embedding_model_version != identity.version
        ):
            raise ValueError("Requested embedding model version is unavailable.")
        query_embedding = service.embed_text(request.query)

        if not any(query_embedding):
            raise ValueError(
                "Query did not contain searchable terms."
            )

        rows = (
            self.document_chunk_repository.search_similar(
                query_embedding=query_embedding,
                top_k=request.top_k,
                identity=identity,
                company_id=request.company_id,
                document_types=request.document_types,
                minimum_similarity=request.minimum_similarity,
            )
        )

        results: list[VectorSearchResultRead] = []

        for (
            document_chunk,
            document,
            distance,
        ) in rows:
            similarity = 1.0 - distance

            normalized_similarity = max(
                -1.0,
                min(1.0, similarity),
            )

            result = VectorSearchResultRead(
                chunk_id=document_chunk.id,
                document_id=document.id,
                company_id=document_chunk.company_id,
                document_title=document.title,
                document_type=document.document_type,
                source_system=document.source_system,
                source_path=document.source_path,
                chunk_index=document_chunk.chunk_index,
                chunk_text=document_chunk.chunk_text,
                token_count=document_chunk.token_count,
                embedding_model=(
                    document_chunk.embedding_model
                ),
                embedding_provider=document_chunk.embedding_provider,
                embedding_model_version=document_chunk.embedding_model_version,
                embedding_dimension=document_chunk.embedding_dimension,
                distance=round(distance, 6),
                similarity=round(
                    normalized_similarity,
                    6,
                ),
            )

            results.append(result)

        return VectorSearchResponse(
            query=request.query,
            company_id=request.company_id,
            top_k=request.top_k,
            result_count=len(results),
            results=results,
            requested_provider=resolution.requested_provider,
            effective_provider=identity.provider,
            effective_model=identity.model,
            effective_model_version=identity.version,
            fallback_used=resolution.fallback_category is not None,
            warnings=(
                [resolution.fallback_category]
                if resolution.fallback_category is not None
                else []
            ),
            requested_embedding=EmbeddingIdentityRead(
                provider=resolution.requested_provider,
                model=(request.embedding_model or identity.model),
                version=(request.embedding_model_version or identity.version),
                dimension=identity.dimension,
            ),
            effective_embedding=EmbeddingIdentityRead(
                provider=identity.provider,
                model=identity.model,
                version=identity.version,
                dimension=identity.dimension,
            ),
        )
