"""API package."""

from app.api.dependencies import get_settings_dependency
from app.api.router import api_router

__all__ = ["api_router", "get_settings_dependency"]
