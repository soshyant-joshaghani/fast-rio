@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

REM Prefer py launcher — bare `python` is often the Windows Store stub.
set "PY="
where py >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
  where python >nul 2>&1
  if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=python"
  )
)
if not defined PY (
  echo Python 3.10+ not found. Install from python.org or enable the py launcher.
  exit /b 1
)

if not exist .venv\Scripts\python.exe (
  echo Creating Python venv at .venv ...
  %PY% -m venv .venv
  if errorlevel 1 exit /b 1
)

call .venv\Scripts\activate.bat
python -m pip install -U pip
if errorlevel 1 exit /b 1
pip install -r requirements.txt
if errorlevel 1 exit /b 1
echo Local environment ready (Python + Rio).
endlocal
