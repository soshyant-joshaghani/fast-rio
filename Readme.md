# Fast-Rio - A Template By Sosha Joshaghani

Minimal full-stack template: **Rio** dashboard + **FastAPI** API + **Postgres** + **Traefik**, on one VM.

Fork or clone this repo when starting a new project. One database, one sample app module, ready to extend. Frontend is pure Python via [rio-ui](https://pypi.org/project/rio-ui/).

## Stack

| Layer | Tech | Dev URL |
|-------|------|---------|
| Frontend | Rio (Python UI) | http://dashboard.localhost |
| Backend | FastAPI + SQLModel + Alembic | http://api.localhost/docs (Swagger) · http://api.localhost/sdoc (Scalar) |
| Database | Postgres 18 | localhost:15432 (dev) |
| Proxy | Traefik 3.6 | http://localhost:18090 |
| Adminer | Adminer (via Traefik) | http://adminer.localhost |

## Quick start (dev)

Starts Postgres + Traefik in Docker, then **uvicorn --reload** and **rio run** on the host (changes apply on save):

```bat
__init__\start-fast-rio-dev.bat
```

```bash
chmod +x __init__/start-fast-rio-dev.sh __init__/setup-local.sh
__init__/start-fast-rio-dev.sh
```

Or via `__ctrl__` (SSH ops + local `dev` commands — see [`__ctrl__/README.md`](__ctrl__/README.md)):

```bat
__ctrl__\fast-rio-ctrl.bat dev run all
```

Stop app processes by closing their terminal windows, or:

```bat
__ctrl__\fast-rio-ctrl.bat dev stop all
```

Stop infrastructure:

```bat
docker compose -f compose.dev.yml down
```

**Port 80/443 conflict:** only one Traefik-on-`:80` stack can run at a time. If compose fails with `Bind for 0.0.0.0:80 failed`, stop the other proxy (e.g. `docker stop fast-game-dev-proxy-1`) or run apps only: `__ctrl__\fast-rio-ctrl.bat dev run apps` (direct `http://localhost:5173` / `http://localhost:18000/docs`).

Or: `__ctrl__\fast-rio-ctrl.bat dev stop all`

### Adminer and database connections

Adminer runs **inside Docker**. Host tools (IDE, local pytest, pgAdmin on Windows) and Adminer use **different** host/port values — both are correct for their context.

| Context | Server | Port | Credentials |
|---------|--------|------|-------------|
| **Adminer** (browser → Docker) | `db` | `5432` (internal) | `POSTGRES_USER` / `POSTGRES_PASSWORD` from `.env` |
| **Host / IDE** (Windows, local scripts) | `localhost` | `15432` (published) | same `.env` values |

**Do not use `localhost:15432` in Adminer** — inside the Adminer container, `localhost` is the Adminer container itself, not Postgres. You will get `Connection refused`.

#### Adminer login (dev)

Open `http://adminer.localhost`. System: **PostgreSQL**.

```
System:   PostgreSQL
Server:   db
Username: postgres          # POSTGRES_USER from .env
Password: <POSTGRES_PASSWORD from .env>
Database: app               # POSTGRES_DB from .env
```

Default values are in `.env.example` (`POSTGRES_DB=app`, `POSTGRES_USER=postgres`).

#### Adminer login (production)

Open `https://adminer.<your-domain>` (see DNS table below). Use the same **Server** (`db`), **Username**, **Password**, and **Database** as in `.env` — not `localhost`.

#### Troubleshooting

- **`Connection refused` on `localhost:15432` in Adminer** — use server `db` and port `5432`.
- **`password authentication failed`** — network is fine; retype the password manually (watch for keyboard layout on `@`). Uncheck “Permanent login” or use a private window if the browser cached old credentials.
- **Password changed in `.env` but login still fails** — Postgres sets the password only when the volume is first created. Either reset it:

  ```bash
  docker compose -f compose.dev.yml exec db psql -U postgres -d app -c "ALTER USER postgres PASSWORD 'your-new-password';"
  ```

  or wipe dev volumes and recreate: `docker compose -f compose.dev.yml down -v` then start again.

Production (single VM):

```bash
# One-time on a fresh Ubuntu VM (Docker, UFW, traefik-public network, .env):
bash __init__/setup-ubuntu.sh

# After editing compose.yml + .env and DNS:
bash __init__/start-fast-rio-prod.sh
```

Windows (Docker Desktop — local prod smoke test only):

```bat
__init__\start-fast-rio-prod.bat
```

### Stop / reset (production)

| Script | What it does |
|--------|----------------|
| `__init__/stop-fast-rio-prod.sh` | Stops all prod containers. Keeps DB, Redis, and SSL. |
| `__init__/reset-fast-rio-prod.sh` | Wipes **db-data** + **redis-data** + app `:prod` images; keeps SSL. |
| `__init__/backup-acme.sh` | SSL → `../.foxg-ssl-backups/fast-rio/acme.json` |
| `__init__/restore-acme.sh` | Restore from parent backup |
| `__init__/prune-docker-build.sh` | Backup SSL, then `docker builder prune -af` |

Windows: `.bat` variants. Start script auto-restores SSL from parent backup if local file is empty.

Before prod: edit `DOMAIN` in `compose.yml`, set secrets in `.env`, and point DNS at the VM (CDN optional — origin is the VM):

| Host | Type | Target | Serves |
|------|------|--------|--------|
| `@` | A | VM IP | `https://example.com` (frontend) |
| `api` | A | VM IP | `https://api.example.com` (backend) |
| `adminer` | A | VM IP | `https://adminer.example.com` (optional) |

## Local tooling (manual)

Root-level dependencies:

```bat
__init__\setup-local.bat
```

- Python: `.venv` + `pip install -r requirements.txt` (includes **`rio-ui[window]`** for local desktop apps via `run_in_window()`)

Run Rio on the host (API via compose or local uvicorn):

```bat
cd frontend
set PUBLIC_API_BASE_URL=http://localhost:18000/api/v1
rio run --port 5173
```

## Tests

```bat
__init__\tests\test-all.bat
__init__\tests\test-backend-all.bat
__init__\tests\test-frontend-all.bat
```

Backend tests run locally with pytest (dev DB on `localhost:15432`). Frontend tests run with pytest against `src.config` helpers.

## Project layout

```
fast-rio/
├── requirements.txt          # Python deps (FastAPI + rio-ui[window])
├── .venv/                    # local Python env
├── __ctrl__/                 # SSH ops + local `dev run all` (see __ctrl__/README.md)
├── compose.dev.yml           # dev infra (db + Traefik); apps run on host
├── compose.yml               # production (includes Traefik + LE)
├── backend/app/
│   ├── api/                  # router aggregation + deps
│   ├── core/                 # config, db, security
│   └── modules/
│       ├── system/           # health-check, private (local)
│       ├── base/             # auth, users, …
│       └── apps/             # per-product modules
├── frontend/
│   ├── rio.toml              # main-module = src
│   └── src/
│       ├── config/           # API_BASE_URL
│       ├── modules/          # shell (auth) + apps/*
│       ├── components/       # RootComponent + Navbar
│       └── pages/            # @rio.page routes
└── tests/
    ├── backend/              # pytest (matches backend module paths)
    └── frontend/             # pytest (config helpers)
```

## Adding features

**Backend:** create `backend/app/modules/apps/<name>/` with `router.py`, optional `models.py`, `schemas.py`, `service.py`, `repository/`. Register in `modules/apps/router.py`.

**Frontend:** add UI under `frontend/src/modules/apps/<name>/` and pages under `frontend/src/pages/`.

**Tests:** mirror paths under `tests/backend/` and `tests/frontend/`.

## Environment

Copy `.env.example` → `.env`. URLs and CORS live in `compose.*.yml`; secrets and DB credentials live in `.env`.

Default superuser (change in `.env`):

- Email: `admin@example.com`
- Password: value of `FIRST_SUPERUSER_PASSWORD`

`PUBLIC_API_BASE_URL` tells the Rio process where FastAPI lives (server-side HTTP from Python components).

## Production notes

- `compose.yml` includes `compose.traefik.yml` with Let's Encrypt (`tls.certresolver=le`).
- Create external network once: `docker network create traefik-public`
- Set `DOMAIN`, `FRONTEND_HOST` (`https://<domain>`), and `BACKEND_CORS_ORIGINS` in `compose.yml`.
- Frontend env: `PUBLIC_API_BASE_URL=http://backend:8000/api/v1` (Docker network; Rio calls FastAPI server-side)
- Traefik routes apex `@` → frontend, `api` → backend (see DNS table above).
