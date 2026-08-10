from fastapi import APIRouter

from app.core.config import settings
from app.modules.system.router.private import private_router
from app.modules.system.router.utils import utils_router
from app.modules.base.router import base_router
from app.modules.apps.router import apps_router

api_router = APIRouter()

# System
api_router.include_router(utils_router)

# Private (local only)
if settings.ENVIRONMENT == "local":
    api_router.include_router(private_router)

# Base platform modules
api_router.include_router(base_router)

# App-specific modules
api_router.include_router(apps_router)
