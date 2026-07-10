"""Top-level API router."""

from fastapi import APIRouter

from app.api import chat, health, hcp, interaction

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(interaction.router)
api_router.include_router(hcp.router)
