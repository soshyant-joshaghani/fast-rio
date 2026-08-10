from fastapi import APIRouter

from app.modules.base.schemas import Message

sample_router = APIRouter(prefix="/sample", tags=["[APPS] Sample"])


@sample_router.get("/", response_model=Message)
def sample_root() -> Message:
    return Message(message="Add your app modules under modules/apps/")
