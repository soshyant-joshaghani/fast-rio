# Backend

FastAPI app under `app/`. Entry point: `app/main.py`.

## Module layout

```
app/
├── api/main.py       # mounts system + base + apps routers
├── core/             # config, db, security
└── modules/
    ├── system/       # health-check, private dev routes
    ├── base/         # platform (auth, users, …)
    └── apps/         # product-specific APIs
```

## Local run (without Docker)

From repo root after `__init__/setup-local.bat`:

```bat
.venv\Scripts\activate
cd backend
set PYTHONPATH=%CD%
uvicorn app.main:app --reload --port 18000
```

Migrations:

```bat
cd backend
set PYTHONPATH=%CD%
alembic -c alembic.ini upgrade head
```

## API docs

| URL | UI |
|-----|-----|
| `/docs` | Swagger UI |
| `/sdoc` | Scalar |

OpenAPI schema: `/api/v1/openapi.json`

## Docker

Built from root `requirements.txt`. Prestart runs migrations + seeds `FIRST_SUPERUSER`.
