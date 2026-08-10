# Frontend (Rio)

Python UI via [rio-ui](https://pypi.org/project/rio-ui/) — no HTML/CSS/JS.

## Layout

```
frontend/
├── rio.toml                 # main-module = src
└── src/
    ├── __init__.py          # rio.App
    ├── config/              # API_BASE_URL
    ├── modules/shell/       # auth shell + helpers
    ├── modules/apps/        # per-app UI modules
    ├── components/          # RootComponent + Navbar
    └── pages/               # @rio.page routes
```

## Dev

From repo root (after `__init__/setup-local`):

```bat
cd frontend
set PUBLIC_API_BASE_URL=http://localhost:18000/api/v1
rio run --port 5173
```

Or use `__init__/start-fast-rio-dev.bat` (starts Traefik + API + Rio).

Traefik: http://dashboard.localhost → Rio :5173

## Production

`Dockerfile` runs `rio run --port 5000 --release`.

Set `PUBLIC_API_BASE_URL` at runtime (compose uses `http://backend:8000/api/v1` on the Docker network).

## Local desktop app

Root `requirements.txt` installs `rio-ui[window]` (pywebview / PySide6). From `frontend/`:

```bat
set PYTHONPATH=%CD%
set PUBLIC_API_BASE_URL=http://localhost:18000/api/v1
python -c "import src; src.app.run_in_window()"
```
