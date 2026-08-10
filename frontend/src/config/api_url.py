"""Pure helper — safe to import from pytest without a Rio session."""


def normalize_api_base_url(value: str | None, fallback: str = "/api/v1") -> str:
    return (value if value is not None else fallback).rstrip("/")
