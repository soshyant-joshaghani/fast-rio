from __future__ import annotations

from pathlib import Path

import rio

from . import components as comps
from .modules.shell.stores.auth import AuthSettings, AuthUser, settings_to_user


async def on_session_start(session: rio.Session) -> None:
    """Restore AuthUser attachment from persisted AuthSettings."""
    settings = session[AuthSettings]
    user = settings_to_user(settings)
    if user is not None:
        session.attach(user)


theme = rio.Theme.from_colors(
    primary_color=rio.Color.from_hex("0ea5e9"),
    secondary_color=rio.Color.from_hex("8b5cf6"),
    background_color=rio.Color.from_hex("09090b"),
    neutral_color=rio.Color.from_hex("18181b"),
    mode="dark",
)

app = rio.App(
    name="fast-rio",
    build=comps.RootComponent,
    theme=theme,
    default_attachments=[AuthSettings()],
    on_session_start=on_session_start,
    assets_dir=Path(__file__).parent / "assets",
)
