"""Resolve foxg-back storage_modes (bundled MinIO vs external Arvan) onto a server dict.

Apply after db_mode so compose_files / start_cmd reflect both axes.
"""

from __future__ import annotations

from typing import Any


def _compose_cmds(files: list[str]) -> dict[str, str]:
    args = " ".join(f"-f {f}" for f in files)
    return {
        "start_cmd": f"docker compose {args} up -d --build",
        "stop_cmd": f"docker compose {args} down --remove-orphans",
        "status_cmd": f"docker compose {args} ps",
    }


def _all_mode_extras(modes: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Collect compose_extra / data_volumes_extra from every storage mode."""
    compose: set[str] = set()
    volumes: set[str] = set()
    for overlay in modes.values():
        if not isinstance(overlay, dict):
            continue
        for f in overlay.get("compose_extra") or []:
            compose.add(f)
        for v in overlay.get("data_volumes_extra") or []:
            volumes.add(v)
    return compose, volumes


def apply_storage_mode(
    server: dict[str, Any],
    mode: str | None = None,
) -> dict[str, Any]:
    """Merge storage_modes overlay onto a copy of server.

    Servers without ``storage_modes`` are returned unchanged.
    Mode resolution: ``mode`` arg → ``server["storage_mode"]`` → ``"external"``.

    Known extras from *all* modes are stripped first, then the selected mode's
    extras are applied — so switching to ``external`` drops MinIO cleanly.
    """
    modes = server.get("storage_modes")
    if not modes or not isinstance(modes, dict):
        return server

    resolved = (mode or server.get("storage_mode") or "external").strip().lower()
    if resolved not in modes:
        allowed = ", ".join(sorted(modes.keys()))
        raise SystemExit(
            f"Server '{server.get('id')}' unknown --storage-mode '{resolved}'. "
            f"Allowed: {allowed}"
        )

    overlay = modes[resolved]
    if not isinstance(overlay, dict):
        raise SystemExit(
            f"Server '{server.get('id')}' storage_modes.{resolved} must be an object"
        )

    out = dict(server)
    out["storage_mode"] = resolved

    strip_compose, strip_volumes = _all_mode_extras(modes)
    files = [f for f in (out.get("compose_files") or []) if f not in strip_compose]
    vols = [v for v in (out.get("data_volumes") or []) if v not in strip_volumes]

    for f in overlay.get("compose_extra") or []:
        if f not in files:
            files.append(f)
    for v in overlay.get("data_volumes_extra") or []:
        if v not in vols:
            vols.append(v)

    out["compose_files"] = files
    out["data_volumes"] = vols
    # Rebuild compose cmds when start/stop are plain `docker compose …`.
    # Keep wrapper scripts (e.g. bash __init__/start-*-prod.sh) intact.
    if files:
        cmds = _compose_cmds(files)
        prev_start = (out.get("start_cmd") or "").strip()
        prev_stop = (out.get("stop_cmd") or "").strip()
        if not prev_start or prev_start.startswith("docker compose"):
            out["start_cmd"] = cmds["start_cmd"]
        if not prev_stop or prev_stop.startswith("docker compose"):
            out["stop_cmd"] = cmds["stop_cmd"]
        out["status_cmd"] = cmds["status_cmd"]

    return out


def apply_storage_mode_to_targets(
    targets: list[dict[str, Any]],
    mode: str | None = None,
) -> list[dict[str, Any]]:
    """Apply storage mode to each target that defines storage_modes."""
    return [apply_storage_mode(s, mode) for s in targets]
