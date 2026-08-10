"""Root layout with persistent navbar + PageView."""

from __future__ import annotations

import rio

from src import components as comps


class RootComponent(rio.Component):
    def build(self) -> rio.Component:
        return rio.Column(
            comps.Navbar(),
            rio.PageView(
                grow_y=True,
                margin=2,
            ),
            grow_y=True,
        )
