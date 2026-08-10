"""Resolve foxg-back db_modes (bundled vs external Postgres) onto a server dict."""

from __future__ import annotations

from typing import Any

# Keys copied from db_modes.<mode> onto the server when applying a mode.
_MODE_KEYS = (
    "compose_files",
    "start_cmd",
    "stop_cmd",
    "status_cmd",
    "env_file",
    "data_volumes",
)


def apply_db_mode(
    server: dict[str, Any],
    mode: str | None = None,
) -> dict[str, Any]:
    """Merge db_modes overlay onto a copy of server.

    Servers without ``db_modes`` are returned unchanged (front/game/eternal-arena).
    Mode resolution: ``mode`` arg → ``server["db_mode"]`` → ``"bundled"``.
    """
    modes = server.get("db_modes")
    if not modes or not isinstance(modes, dict):
        return server

    resolved = (mode or server.get("db_mode") or "bundled").strip().lower()
    if resolved not in modes:
        allowed = ", ".join(sorted(modes.keys()))
        raise SystemExit(
            f"Server '{server.get('id')}' unknown --db-mode '{resolved}'. "
            f"Allowed: {allowed}"
        )

    overlay = modes[resolved]
    if not isinstance(overlay, dict):
        raise SystemExit(
            f"Server '{server.get('id')}' db_modes.{resolved} must be an object"
        )

    out = dict(server)
    out["db_mode"] = resolved
    for key in _MODE_KEYS:
        if key in overlay:
            out[key] = overlay[key]
    return out


def apply_db_mode_to_targets(
    targets: list[dict[str, Any]],
    mode: str | None = None,
) -> list[dict[str, Any]]:
    """Apply db mode to each target that defines db_modes."""
    return [apply_db_mode(s, mode) for s in targets]
