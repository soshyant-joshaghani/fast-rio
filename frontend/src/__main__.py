"""Run the Rio dashboard as a web server (used by Docker / uvicorn)."""

from __future__ import annotations

import os

from src import app

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    app.run_as_web_server(host=host, port=port)
