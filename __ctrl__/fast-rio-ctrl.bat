@echo off
setlocal EnableExtensions
cd /d "%~dp0"

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
  echo [fast-rio-ctrl] Python 3.10+ not found. Install from python.org or enable the py launcher.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [fast-rio-ctrl] Creating .venv and installing requirements...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo Failed to create .venv
    pause
    exit /b 1
  )
  ".venv\Scripts\pip.exe" install -r requirements.txt
  if errorlevel 1 (
    echo Failed to install requirements.txt
    pause
    exit /b 1
  )
)

set "CTRL_PY=.venv\Scripts\python.exe"

REM No args: interactive REPL (stays open). With args: run once.
if "%~1"=="" (
  "%CTRL_PY%" main.py
  echo.
  pause
  exit /b %ERRORLEVEL%
)

"%CTRL_PY%" main.py %*
set ERR=%ERRORLEVEL%
if not "%ERR%"=="0" (
  echo.
  echo Command failed with exit code %ERR%
  pause
)
exit /b %ERR%
