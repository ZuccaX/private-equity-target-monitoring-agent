import contextvars
import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import Request, Response


request_id_context: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
agent_run_id_context: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "agent_run_id", default=None
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
            "agent_run_id": agent_run_id_context.get(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    setattr(handler, "_pe_agent_json_handler", True)
    root_logger = logging.getLogger()
    root_logger.handlers = [
        existing_handler
        for existing_handler in root_logger.handlers
        if not getattr(existing_handler, "_pe_agent_json_handler", False)
    ]
    root_logger.addHandler(handler)
    root_logger.setLevel(level.upper())


async def request_context_middleware(
    request: Request,
    call_next: Any,
) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    agent_run_id = request.headers.get("X-Agent-Run-ID")
    request_token = request_id_context.set(request_id)
    run_token = agent_run_id_context.set(agent_run_id)
    logger = logging.getLogger("api.request")

    try:
        response = await call_next(request)
        logger.info(
            "%s %s %s",
            request.method,
            request.url.path,
            response.status_code,
        )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as error:
        logger.error(
            "%s %s failed error_type=%s",
            request.method,
            request.url.path,
            type(error).__name__,
        )
        raise
    finally:
        request_id_context.reset(request_token)
        agent_run_id_context.reset(run_token)
