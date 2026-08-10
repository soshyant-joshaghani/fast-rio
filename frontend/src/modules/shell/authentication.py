"""Login / signup form — mirrors Authentication.svelte."""

from __future__ import annotations

import re

import rio

from src.modules.shell.stores import auth as auth_store
from src.modules.shell.utils import auth_api


class Authentication(rio.Component):
    """Email/password login and private-route signup against FastAPI."""

    active_tab: str = "login"  # "login" | "signup"
    email: str = ""
    password: str = ""
    full_name: str = ""
    error: str = ""
    is_loading: bool = False

    def _switch_tab(self, tab: str) -> None:
        self.active_tab = tab
        self.error = ""
        self.email = ""
        self.password = ""
        self.full_name = ""

    async def _after_auth(self, token: str) -> None:
        user = await auth_api.fetch_current_user(token)
        auth_store.apply_login(self.session, token, user)

    async def _handle_login(self, _event: rio.TextInputConfirmEvent | None = None) -> None:
        self.error = ""
        self.is_loading = True
        self.force_refresh()
        try:
            token = await auth_api.login_with_password(self.email, self.password)
            await self._after_auth(token)
        except Exception as exc:
            self.error = str(exc) or "Unable to connect to server. Please try again."
        finally:
            self.is_loading = False

    async def _handle_signup(self, _event: rio.TextInputConfirmEvent | None = None) -> None:
        self.error = ""
        self.is_loading = True
        self.force_refresh()

        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", self.email):
            self.error = "Invalid email format"
            self.is_loading = False
            return
        if not self.password or len(self.password) < 8:
            self.error = "Password must be at least 8 characters long"
            self.is_loading = False
            return

        try:
            await auth_api.signup_with_private_route(
                self.email, self.password, self.full_name
            )
            token = await auth_api.login_with_password(self.email, self.password)
            await self._after_auth(token)
        except Exception as exc:
            self.error = str(exc) or "Unable to connect to server. Please try again."
        finally:
            self.is_loading = False

    def build(self) -> rio.Component:
        tab_row = rio.Row(
            rio.Button(
                "Login",
                on_press=lambda: self._switch_tab("login"),
                style="major" if self.active_tab == "login" else "minor",
                grow_x=True,
            ),
            rio.Button(
                "Sign up",
                on_press=lambda: self._switch_tab("signup"),
                style="major" if self.active_tab == "signup" else "minor",
                grow_x=True,
            ),
            spacing=0.5,
        )

        if self.active_tab == "login":
            form = rio.Column(
                rio.TextInput(
                    text=self.bind().email,
                    label="Email",
                    is_sensitive=not self.is_loading,
                    on_confirm=self._handle_login,
                ),
                rio.TextInput(
                    text=self.bind().password,
                    label="Password",
                    is_secret=True,
                    is_sensitive=not self.is_loading,
                    on_confirm=self._handle_login,
                ),
                rio.Button(
                    "Logging in…" if self.is_loading else "Login",
                    on_press=self._handle_login,
                    is_loading=self.is_loading,
                    style="major",
                ),
                rio.Button(
                    "No account? Sign up",
                    on_press=lambda: self._switch_tab("signup"),
                    style="plain-text",
                ),
                spacing=1,
            )
        else:
            form = rio.Column(
                rio.TextInput(
                    text=self.bind().email,
                    label="Email",
                    is_sensitive=not self.is_loading,
                    on_confirm=self._handle_signup,
                ),
                rio.TextInput(
                    text=self.bind().full_name,
                    label="Full name (optional)",
                    is_sensitive=not self.is_loading,
                ),
                rio.TextInput(
                    text=self.bind().password,
                    label="Password (min. 8 characters)",
                    is_secret=True,
                    is_sensitive=not self.is_loading,
                    on_confirm=self._handle_signup,
                ),
                rio.Button(
                    "Creating account…" if self.is_loading else "Create account",
                    on_press=self._handle_signup,
                    is_loading=self.is_loading,
                    color="success",
                ),
                rio.Button(
                    "Already registered? Login",
                    on_press=lambda: self._switch_tab("login"),
                    style="plain-text",
                ),
                spacing=1,
            )

        children: list[rio.Component] = [
            rio.Text("Welcome back", style="heading2", justify="center"),
            rio.Text(
                "POST /api/v1/private/users/ · dev signup",
                style="dim",
                justify="center",
            ),
            tab_row,
            form,
        ]
        if self.error:
            children.append(rio.Banner(text=self.error, style="danger"))

        return rio.Column(*children, spacing=1.5, grow_x=True)
