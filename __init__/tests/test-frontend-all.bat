@echo off
setlocal
cd /d "%~dp0..\.."
call __init__\setup-local.bat
echo [fast-rio] Frontend tests (pytest)
echo.
call .venv\Scripts\activate.bat
set "PYTHONPATH=%CD%\frontend"
pytest tests\frontend -v
if errorlevel 1 goto :fail
echo.
echo Frontend tests passed.
goto :done
:fail
echo.
echo Frontend tests failed.
pause
exit /b 1
:done
endlocal
