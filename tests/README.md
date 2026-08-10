# Tests

- `backend/` — pytest against FastAPI (`tests/backend/` paths match `backend/app/modules/`)
- `frontend/` — pytest for Rio config helpers (`src.config`)

Run via `__init__/tests/*.bat` or:

```bat
.venv\Scripts\activate
set PYTHONPATH=frontend
pytest tests\frontend -v

cd backend
set PYTHONPATH=.;..\tests\backend
pytest ..\tests\backend\ -v
```

Backend tests need the dev DB (`compose.dev.yml` → `localhost:15432`).
