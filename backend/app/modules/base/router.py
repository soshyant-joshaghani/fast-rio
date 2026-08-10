from fastapi import APIRouter

from app.modules.base.auth.router import auth_router

base_router = APIRouter(prefix="/base")

# Auth — single login endpoint for all users including SuperAdmin
base_router.include_router(auth_router)

# Add platform modules here (users, items, payments, …)
