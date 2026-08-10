from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.modules.base.users import crud
from app.modules.base.users.models import User, UserCreate

engine = create_engine(str(settings.CORE_SQLALCHEMY_DATABASE_URI))


def init_db(session: Session) -> None:
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        crud.create_user(session=session, user_create=user_in)
