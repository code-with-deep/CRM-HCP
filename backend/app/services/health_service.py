"""Infrastructure health check service."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class HealthService:
    """Evaluate application and dependency health."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def check_database(self, session: AsyncSession) -> str:
        """Verify database connectivity."""
        try:
            await session.execute(text("SELECT 1"))
            return "connected"
        except Exception as exc:
            logger.error("Database health check failed: %s", str(exc), exc_info=exc)
            return "disconnected"

    async def get_health_status(self, session: AsyncSession) -> dict[str, str]:
        """Return aggregated health information."""
        database_status = await self.check_database(session)
        overall_status = "healthy" if database_status == "connected" else "degraded"

        return {
            "name": self._settings.APP_NAME,
            "version": self._settings.APP_VERSION,
            "status": overall_status,
            "database": database_status,
        }

    def get_application_info(self) -> dict[str, str]:
        """Return static application metadata."""
        return {
            "name": self._settings.APP_NAME,
            "version": self._settings.APP_VERSION,
            "status": "running",
        }
