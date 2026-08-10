"""API base URL for the FastAPI backend.

Dev (Traefik): browser hits dashboard.localhost; Python server-side calls
use host.docker.internal or localhost:18000 via PUBLIC_API_BASE_URL.
"""

from __future__ import annotations

import os

from .api_url import normalize_api_base_url

API_BASE_URL = normalize_api_base_url(os.environ.get("PUBLIC_API_BASE_URL"))
