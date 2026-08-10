@echo off
setlocal
cd /d "%~dp0..\.."
echo [fast-rio] Backend tests (pytest + coverage)
echo Requires dev DB: __init__\start-fast-rio-dev.bat (or compose.dev.yml db up)
echo.
call __init__\setup-local.bat
if errorlevel 1 exit /b 1
cd backend
set PYTHONPATH=%CD%;..\tests\backend
call ..\.venv\Scripts\python.exe app\tests_pre_start.py
if errorlevel 1 goto :fail
call ..\.venv\Scripts\coverage.exe run -m pytest ..\tests\backend\
if errorlevel 1 goto :fail
call ..\.venv\Scripts\coverage.exe report
echo.
echo Backend tests passed.
goto :done
:fail
echo.
echo Backend tests failed.
pause
exit /b 1
:done
endlocal
