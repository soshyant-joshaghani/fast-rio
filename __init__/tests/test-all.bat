@echo off
setlocal
cd /d "%~dp0..\.."
set COMPOSE=compose.dev.yml
echo [fast-rio] All tests (backend + frontend)
echo Requires dev stack: __init__\start-fast-rio-dev.bat
echo.
call __init__\tests\test-backend-all.bat
if errorlevel 1 goto :fail
call __init__\tests\test-frontend-all.bat
if errorlevel 1 goto :fail
echo.
echo All tests passed.
goto :done
:fail
echo.
echo Tests failed.
pause
exit /b 1
:done
pause
endlocal
