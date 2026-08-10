from fastapi import APIRouter

from app.modules.apps.sample.router import sample_router

apps_router = APIRouter()

# Add app routers here
apps_router.include_router(sample_router)
