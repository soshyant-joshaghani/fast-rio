@echo off
setlocal
cd /d "%~dp0.."
if not exist .env copy /Y .env.example .env >nul 2>&1
if not exist letsencrypt mkdir letsencrypt
if not exist letsencrypt\acme.json type nul > letsencrypt\acme.json
docker network inspect traefik-public >nul 2>&1 || docker network create traefik-public
docker compose up -d --build
if errorlevel 1 exit /b 1
echo.
echo fast-rio production stack started.
echo Update DOMAIN in compose.yml, ACME email in compose.traefik.yml, and DNS before going live.
pause
endlocal
