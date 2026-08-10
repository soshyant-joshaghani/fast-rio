"""Shell navbar — mirrors +layout.svelte header."""

from __future__ import annotations

import rio

from src.modules.shell import APP_NAME
from src.modules.shell.stores import auth as auth_store
from src.modules.shell.stores.auth import AuthUser


class Navbar(rio.Component):
    def build(self) -> rio.Component:
        right: rio.Component
        if auth_store.is_authenticated(self.session):
            try:
                user = self.session[AuthUser]
            except KeyError:
                settings = self.session[auth_store.AuthSettings]
                user = auth_store.settings_to_user(settings)
            if user is not None:
                role = "SuperAdmin" if user.is_superuser else "User"
                right = rio.Column(
                    rio.Text(user.email, justify="right"),
                    rio.Text(role, style="dim", justify="right"),
                    spacing=0.2,
                    align_x=1,
                )
            else:
                right = rio.Spacer()
        else:
            right = rio.Spacer()

        return rio.Rectangle(
            content=rio.Row(
                rio.Column(
                    rio.Text("DASHBOARD", style="dim"),
                    rio.Text(APP_NAME, style="heading2"),
                    spacing=0.2,
                ),
                rio.Spacer(),
                right,
                margin=1.5,
            ),
            fill=rio.Color.from_hex("09090b"),
            stroke_width=0.05,
            stroke_color=rio.Color.from_hex("1e293b"),
        )
