"""Application health and metadata endpoints."""

from fastapi import APIRouter, status

from app.api.dependencies import DbSessionDep, SettingsDep
from app.schemas.common import ApplicationInfoResponse, HealthCheckResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


@router.get(
    "/",
    response_model=ApplicationInfoResponse,
    summary="Application information",
)
async def get_application_info(settings: SettingsDep) -> ApplicationInfoResponse:
    """Return application name, version, and runtime status."""
    health_service = HealthService(settings)
    info = health_service.get_application_info()
    return ApplicationInfoResponse(**info)


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    status_code=status.HTTP_200_OK,
)
async def health_check(
    settings: SettingsDep,
    session: DbSessionDep,
) -> HealthCheckResponse:
    """Return application health including database connectivity."""
    health_service = HealthService(settings)
    health = await health_service.get_health_status(session)
    return HealthCheckResponse(**health)
