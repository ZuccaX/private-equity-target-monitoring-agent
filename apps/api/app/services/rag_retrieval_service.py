import hashlib
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import DependencyUnavailableError
from app.models.audit_log import AuditLog
from app.models.investment_mandate import InvestmentMandate
from app.models.trigger import Trigger
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.company_repository import CompanyRepository
from app.schemas.vector_search import (
    RAGRetrievalRequest,
    RAGRetrievalResponse,
    VectorSearchRequest,
)
from app.services.rag_context_service import RAGContextService
from app.services.rag_query_service import RAGQueryService
from app.services.vector_search_service import (
    VectorSearchService,
)


class RAGRetrievalService:
    def __init__(
        self,
        db: Session,
        vector_search_service: VectorSearchService | None = None,
    ) -> None:
        self.db = db
        self.vector_search_service = (
            vector_search_service or VectorSearchService(db)
        )
        self.company_repository = CompanyRepository(db)
        self.audit_repository = AuditLogRepository(db)
        self.query_service = RAGQueryService()
        self.context_service = RAGContextService()

    def retrieve(
        self,
        request: RAGRetrievalRequest,
    ) -> RAGRetrievalResponse:
        company = self.company_repository.get_by_id(request.company_id)
        if company is None:
            raise ValueError(f"Company not found: {request.company_id}")
        mandate = (
            self.db.query(InvestmentMandate)
            .filter(InvestmentMandate.id == company.mandate_id)
            .first()
            if company.mandate_id is not None
            else None
        )
        triggers = (
            self.db.query(Trigger)
            .filter(Trigger.company_id == company.id)
            .order_by(Trigger.detected_at.desc())
            .limit(5)
            .all()
        )
        retrieval_query = self.query_service.build(
            user_query=request.query,
            company=company,
            mandate=mandate,
            triggers=triggers,
        )
        search_response = (
            self.vector_search_service.search(
                VectorSearchRequest(
                    query=retrieval_query,
                    company_id=request.company_id,
                    top_k=request.top_k,
                    document_types=request.document_types,
                    minimum_similarity=(
                        request.minimum_similarity
                        if request.minimum_similarity is not None
                        else settings.vector_min_similarity
                    ),
                )
            )
        )
        built = self.context_service.build(
            search_response.results,
            max_words=settings.rag_max_context_words,
        )
        query_digest = hashlib.sha256(retrieval_query.encode("utf-8")).hexdigest()
        try:
            self.audit_repository.create(
                AuditLog(
                    entity_type="rag_retrieval",
                    entity_id=company.id,
                    action="retrieve",
                    actor_type="system",
                    after_data={
                        "query_digest": query_digest,
                        "requested_provider": search_response.requested_provider,
                        "effective_provider": search_response.effective_provider,
                        "fallback_used": search_response.fallback_used,
                        "result_count": len(built.sources),
                        "chunk_ids": [item.chunk_id for item in built.sources],
                    },
                )
            )
            self.db.commit()
        except Exception as error:
            self.db.rollback()
            raise DependencyUnavailableError(
                "Retrieval audit persistence failed; no context was returned."
            ) from error

        logging.getLogger("rag.retrieval").info(
            "retrieval company_id=%s requested_provider=%s "
            "effective_provider=%s fallback=%s result_count=%s query_digest=%s",
            company.id,
            search_response.requested_provider,
            search_response.effective_provider,
            search_response.fallback_used,
            len(built.sources),
            query_digest[:16],
        )

        return RAGRetrievalResponse(
            query=request.query,
            company_id=search_response.company_id,
            top_k=search_response.top_k,
            result_count=len(built.sources),
            context=built.context,
            sources=built.sources,
            status="ok" if built.sources else "empty",
            minimum_similarity=request.minimum_similarity,
            context_word_budget=settings.rag_max_context_words,
            citations=built.citations,
            requested_provider=search_response.requested_provider,
            effective_provider=search_response.effective_provider,
            effective_model=search_response.effective_model,
            effective_model_version=search_response.effective_model_version,
            fallback_used=search_response.fallback_used,
            fallback_reason=(
                search_response.warnings[0]
                if search_response.fallback_used and search_response.warnings
                else None
            ),
            warnings=list(
                dict.fromkeys(search_response.warnings + built.warnings)
            ),
            requested_embedding=search_response.requested_embedding,
            effective_embedding=search_response.effective_embedding,
        )
