"""Application health and metadata endpoints."""

import time

from fastapi import APIRouter, Request, status

from app.api.response import success_response
from app.core.dependencies import DbSessionDep, SettingsDep
from app.schemas.common import ApplicationInfoResponse, HealthCheckResponse
from app.schemas.responses import ApiResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


@router.get(
    "/",
    response_model=ApiResponse[ApplicationInfoResponse],
    summary="Application information",
)
async def get_application_info(
    request: Request,
    settings: SettingsDep,
) -> ApiResponse[ApplicationInfoResponse]:
    """Return application name, version, and runtime status."""
    start_time = time.perf_counter()
    health_service = HealthService(settings)
    info = ApplicationInfoResponse(**health_service.get_application_info())
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return success_response(
        request=request,
        message="Application metadata retrieved successfully.",
        data=info,
        execution_time_ms=elapsed_ms,
    )


@router.get(
    "/health",
    response_model=ApiResponse[HealthCheckResponse],
    summary="Health check",
    status_code=status.HTTP_200_OK,
)
async def health_check(
    request: Request,
    settings: SettingsDep,
    session: DbSessionDep,
) -> ApiResponse[HealthCheckResponse]:
    """Return application health including database connectivity."""
    start_time = time.perf_counter()
    health_service = HealthService(settings)
    health = HealthCheckResponse(**await health_service.get_health_status(session))
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return success_response(
        request=request,
        message="Health check completed successfully.",
        data=health,
        execution_time_ms=elapsed_ms,
    )
