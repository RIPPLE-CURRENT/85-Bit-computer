@echo off
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
    py -3 simulator.py
    goto end
)
where python >nul 2>&1
if %errorlevel%==0 (
    python simulator.py
    goto end
)
echo Python 3 not found. Install it from https://www.python.org/downloads/
pause
exit /b 1
:end
if errorlevel 1 pause
