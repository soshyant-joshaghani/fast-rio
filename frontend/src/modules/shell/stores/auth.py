"""Auth state persisted via Rio UserSettings (client-side storage)."""

from __future__ import annotations

from dataclasses import dataclass

import rio


@dataclass
class AuthUser:
    email: str
    id: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class AuthSettings(rio.UserSettings):
    """Persisted auth token + user snapshot (replaces localStorage)."""

    auth_token: str = ""
    user_email: str = ""
    user_id: str = ""
    user_full_name: str = ""
    is_superuser: bool = False
    is_active: bool = True


def settings_to_user(settings: AuthSettings) -> AuthUser | None:
    if not settings.auth_token or not settings.user_email:
        return None
    return AuthUser(
        id=settings.user_id or None,
        email=settings.user_email,
        full_name=settings.user_full_name or None,
        is_superuser=settings.is_superuser,
        is_active=settings.is_active,
    )


def apply_login(session: rio.Session, token: str, user: AuthUser) -> None:
    settings = session[AuthSettings]
    settings.auth_token = token
    settings.user_email = user.email
    settings.user_id = user.id or ""
    settings.user_full_name = user.full_name or ""
    settings.is_superuser = bool(user.is_superuser)
    settings.is_active = True if user.is_active is None else bool(user.is_active)
    session.attach(settings)
    session.attach(user)


def apply_logout(session: rio.Session) -> None:
    settings = session[AuthSettings]
    settings.auth_token = ""
    settings.user_email = ""
    settings.user_id = ""
    settings.user_full_name = ""
    settings.is_superuser = False
    settings.is_active = True
    session.attach(settings)
    try:
        session.detach(AuthUser)
    except KeyError:
        pass


def get_token(session: rio.Session) -> str | None:
    token = session[AuthSettings].auth_token
    return token or None


def is_authenticated(session: rio.Session) -> bool:
    return bool(session[AuthSettings].auth_token and session[AuthSettings].user_email)
