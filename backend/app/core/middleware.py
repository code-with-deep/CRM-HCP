"""HTTP middleware for request tracing and timing."""

import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-Id"
CORRELATION_ID_HEADER = "X-Correlation-Id"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request/correlation IDs and log request timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
        correlation_id = request.headers.get(CORRELATION_ID_HEADER, request_id)
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        start_time = time.perf_counter()
        logger.info(
            "Incoming request %s %s [request_id=%s correlation_id=%s]",
            request.method,
            request.url.path,
            request_id,
            correlation_id,
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed %s %s in %.2fms [request_id=%s]: %s",
                request.method,
                request.url.path,
                elapsed_ms,
                request_id,
                str(exc),
                exc_info=exc,
            )
            raise

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Completed request %s %s status=%s in %.2fms [request_id=%s]",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )

        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        return response
