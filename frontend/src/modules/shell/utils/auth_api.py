"""HTTP helpers talking to the FastAPI auth endpoints."""

from __future__ import annotations

import typing as t

import httpx

from src.config.backend import API_BASE_URL
from src.modules.shell.stores.auth import AuthUser


def format_api_error(detail: t.Any, fallback: str) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        parts: list[str] = []
        for item in detail:
            if isinstance(item, dict) and "msg" in item:
                parts.append(str(item["msg"]))
            else:
                parts.append(str(item))
        return ", ".join(parts)
    return fallback


async def fetch_current_user(token: str) -> AuthUser:
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(
            f"{API_BASE_URL}/base/login/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    if res.status_code >= 400:
        raise RuntimeError("Failed to fetch user profile")
    data = res.json()
    return AuthUser(
        id=str(data["id"]) if data.get("id") is not None else None,
        email=data["email"],
        full_name=data.get("full_name"),
        is_active=data.get("is_active"),
        is_superuser=data.get("is_superuser"),
    )


async def login_with_password(email: str, password: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(
            f"{API_BASE_URL}/base/login/access-token",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if res.status_code >= 400:
        try:
            body = res.json()
        except Exception:
            body = {}
        raise RuntimeError(format_api_error(body.get("detail"), "Invalid email or password"))
    return str(res.json()["access_token"])


async def signup_with_private_route(
    email: str,
    password: str,
    full_name: str | None = None,
) -> None:
    payload: dict[str, str] = {
        "email": email.strip(),
        "password": password,
    }
    if full_name and full_name.strip():
        payload["full_name"] = full_name.strip()

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(
            f"{API_BASE_URL}/private/users/",
            json=payload,
        )
    if res.status_code >= 400:
        try:
            body = res.json()
        except Exception:
            body = {}
        raise RuntimeError(format_api_error(body.get("detail"), "Sign up failed"))
