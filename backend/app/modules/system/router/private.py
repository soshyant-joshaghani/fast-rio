from typing import Any

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.core.security import get_password_hash
from app.modules.base.schemas import Message, PrivateUserCreate
from app.modules.base.users.models import User, UserPublic

private_router = APIRouter(tags=["[SYSTEM] System - Private"], prefix="/private")


@private_router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    """Create a user (local dev only)."""
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@private_router.get("/ping/", response_model=Message)
def private_ping() -> Message:
    return Message(message="private ok")
