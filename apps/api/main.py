from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes_agent_runs import router as agent_runs_router
from app.api.routes_audit import router as audit_router
from app.api.routes_companies import router as companies_router
from app.api.routes_crm import router as crm_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_documents import router as documents_router
from app.api.routes_drafts import router as drafts_router
from app.api.routes_feedback import router as feedback_router
from app.api.routes_health import router as health_router
from app.api.routes_integrations import router as integrations_router
from app.api.routes_mandates import router as mandates_router
from app.api.routes_news_articles import router as news_articles_router
from app.api.routes_pipeline import router as pipeline_router
from app.api.routes_rag import router as rag_router
from app.api.routes_triggers import router as triggers_router
from app.api.routes_vector_search import router as vector_search_router
from app.core.config import settings
from app.core.exceptions import DomainError
from app.core.logging import configure_logging, request_context_middleware


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    application = FastAPI(
        title=settings.app_name,
        description="Backend API for the PE Origination Agent Platform.",
        version=settings.app_version,
    )

    application.middleware("http")(request_context_middleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(DomainError)
    async def handle_domain_error(
        _request: Request, error: DomainError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.message, "code": error.code},
        )

    for router in (
        health_router,
        companies_router,
        mandates_router,
        pipeline_router,
        agent_runs_router,
        drafts_router,
        feedback_router,
        audit_router,
        integrations_router,
        news_articles_router,
        triggers_router,
        dashboard_router,
        crm_router,
        documents_router,
        vector_search_router,
        rag_router,
    ):
        application.include_router(router)

    return application


app = create_app()
