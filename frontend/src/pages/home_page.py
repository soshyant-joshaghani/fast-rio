"""Home / auth test page — mirrors routes/+page.svelte."""

from __future__ import annotations

import httpx
import rio

from src.config.backend import API_BASE_URL
from src.modules.shell.authentication import Authentication
from src.modules.shell.stores import auth as auth_store
from src.modules.shell.stores.auth import AuthUser
from src.modules.shell.utils import auth_api


@rio.page(
    name="Home",
    url_segment="",
)
class HomePage(rio.Component):
    health: str = "…"
    sample: str = "…"
    api_error: str = ""
    me_check: str = "not tested"
    me_loading: bool = False
    _probed: bool = False

    @rio.event.on_populate
    async def _probe_api(self) -> None:
        if self._probed:
            return
        self._probed = True
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                health_res = await client.get(f"{API_BASE_URL}/utils/health-check/")
                if health_res.is_success:
                    self.health = str(health_res.json())
                else:
                    self.health = f"HTTP {health_res.status_code}"

                sample_res = await client.get(f"{API_BASE_URL}/sample/")
                if sample_res.is_success:
                    body = sample_res.json()
                    self.sample = body.get("message", "ok")
                else:
                    self.sample = f"HTTP {sample_res.status_code}"
        except Exception as exc:
            self.api_error = str(exc) or "Request failed"
            self.health = "ERR"

    async def _test_me(self) -> None:
        token = auth_store.get_token(self.session)
        if not token:
            self.me_check = "no token in store"
            return
        self.me_loading = True
        self.force_refresh()
        try:
            user = await auth_api.fetch_current_user(token)
            suffix = " (superuser)" if user.is_superuser else ""
            self.me_check = f"{user.email}{suffix}"
        except Exception as exc:
            self.me_check = str(exc) or "request failed"
        finally:
            self.me_loading = False

    def _logout(self) -> None:
        auth_store.apply_logout(self.session)
        self.me_check = "not tested"

    def _signed_in_panel(self, user: AuthUser) -> rio.Component:
        role = "SuperAdmin" if user.is_superuser else "User"
        return rio.Column(
            rio.Banner(text="Signed in", style="success"),
            rio.Text(user.email),
            rio.Text(f"Role: {role}", style="dim"),
            rio.Row(
                rio.Button(
                    "Calling /me…" if self.me_loading else "Test GET /base/login/me",
                    on_press=self._test_me,
                    is_loading=self.me_loading,
                    color="secondary",
                ),
                rio.Button(
                    "Log out",
                    on_press=self._logout,
                    color="danger",
                ),
                spacing=0.8,
            ),
            rio.Card(
                rio.Column(
                    rio.Text("RESPONSE", style="dim"),
                    rio.Text(self.me_check),
                    spacing=0.4,
                    margin=1,
                ),
            ),
            spacing=1,
        )

    def build(self) -> rio.Component:
        user: AuthUser | None = None
        if auth_store.is_authenticated(self.session):
            try:
                user = self.session[AuthUser]
            except KeyError:
                user = auth_store.settings_to_user(self.session[auth_store.AuthSettings])

        auth_body: rio.Component
        if user is not None:
            auth_body = self._signed_in_panel(user)
        else:
            auth_body = Authentication()

        overview = rio.Card(
            rio.Column(
                rio.Text("OVERVIEW", style="dim"),
                rio.Text("Auth test page", style="heading2"),
                rio.Markdown(
                    "Session restores from **AuthSettings** on load. "
                    "Default superuser: `admin@example.com`"
                ),
                spacing=0.8,
                margin=1.5,
            ),
        )

        auth_card = rio.Card(
            rio.Column(
                rio.Text("AUTH · Authentication", style="heading3"),
                auth_body,
                spacing=1,
                margin=1.5,
            ),
        )

        health_status = self.api_error or self.health
        api_cards = rio.Column(
            rio.Card(
                rio.Column(
                    rio.Text("GET /api/v1/utils/health-check/", style="dim"),
                    rio.Text(health_status),
                    spacing=0.6,
                    margin=1.2,
                ),
            ),
            rio.Card(
                rio.Column(
                    rio.Text("GET /api/v1/sample/", style="dim"),
                    rio.Text(self.sample),
                    spacing=0.6,
                    margin=1.2,
                ),
            ),
            rio.Card(
                rio.Column(
                    rio.Text("OPERATIONS", style="dim"),
                    rio.Markdown(
                        "- `GET` `/utils/health-check/`\n"
                        "- `POST` `/base/login/access-token`\n"
                        "- `GET` `/base/login/me`"
                    ),
                    spacing=0.6,
                    margin=1.2,
                ),
            ),
            spacing=1,
            grow_x=True,
        )

        return rio.Column(
            overview,
            rio.Row(
                auth_card,
                api_cards,
                spacing=1.5,
                proportions=[1, 1],
            ),
            spacing=1.5,
            align_y=0,
        )
