@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
if not exist .env copy /Y .env.example .env >nul 2>&1

call __init__\setup-local.bat
if errorlevel 1 exit /b 1

echo [fast-rio] Starting dev infrastructure (db, proxy, adminer)...
docker compose -f compose.dev.yml up -d db adminer
if errorlevel 1 exit /b 1
REM Recreate proxy so Traefik re-reads dynamic.dev.yml (Windows bind mounts skip fsnotify).
docker compose -f compose.dev.yml up -d --force-recreate --no-deps proxy
if errorlevel 1 exit /b 1

echo [fast-rio] Waiting for Postgres...
:wait_db
docker compose -f compose.dev.yml exec -T db pg_isready -U postgres >nul 2>&1
if errorlevel 1 (
  timeout /t 2 /nobreak >nul
  goto wait_db
)

set "ROOT=%CD%"

echo [fast-rio] Running migrations + seed (local prestart)...
cd /d "%ROOT%\backend"
call "%ROOT%\.venv\Scripts\activate.bat"
set "PYTHONPATH=%CD%"
python app\backend_pre_start.py
if errorlevel 1 exit /b 1
alembic -c alembic.ini upgrade head
if errorlevel 1 exit /b 1
python app\initial_data.py
if errorlevel 1 exit /b 1
cd /d "%ROOT%"

echo [fast-rio] Starting backend (uvicorn --reload) and frontend (rio run)...
REM Avoid nested-quote breakage in `start … cmd /k "…"` — use ^& chaining.
start "fast-rio-backend" cmd /k cd /d "%ROOT%\backend" ^& call "%ROOT%\.venv\Scripts\activate.bat" ^& set "PYTHONPATH=%ROOT%\backend" ^& python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 18000
start "fast-rio-frontend" cmd /k cd /d "%ROOT%\frontend" ^& call "%ROOT%\.venv\Scripts\activate.bat" ^& set "PYTHONPATH=%ROOT%\frontend" ^& set "PUBLIC_API_BASE_URL=http://localhost:18000/api/v1" ^& python -m rio run --port 5173 --public

echo.
echo Dev stack ready (hot reload on save):
echo   Dashboard: http://dashboard.localhost
echo   API docs:  http://api.localhost/docs  (Swagger)
echo   Scalar:    http://api.localhost/sdoc
echo   Adminer:   http://adminer.localhost
echo   Traefik:   http://localhost:18090
echo.
echo Direct (no Traefik): http://localhost:5173  http://localhost:18000/docs
echo Close the backend/frontend terminal windows to stop app processes.
echo Run: docker compose -f compose.dev.yml down
echo Or:  __ctrl__\fast-rio-ctrl.bat dev stop all
pause
endlocal
