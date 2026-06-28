@echo off
setlocal
cd /d "%~dp0"

set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"
set "VENV_PYTHONW=%CD%\.venv\Scripts\pythonw.exe"

if exist "%VENV_PYTHON%" goto ensure_runtime

echo StemPy needs to create its private runtime.
echo This one-time setup downloads Python packages and may use several GB.
choice /M "Continue"
if errorlevel 2 exit /b 1

set "BOOTSTRAP_PYTHON="
for /f "delims=" %%P in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do set "BOOTSTRAP_PYTHON=%%P"
if defined BOOTSTRAP_PYTHON goto create_runtime

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set "BOOTSTRAP_PYTHON=%LocalAppData%\Programs\Python\Python312\python.exe"
    goto create_runtime
)

where winget >nul 2>nul
if errorlevel 1 (
    echo Python 3.12 and winget were not found.
    echo Install Python 3.12 from python.org, then run this file again.
    pause
    exit /b 1
)

echo Installing Python 3.12...
winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
if errorlevel 1 goto setup_failed
set "BOOTSTRAP_PYTHON=%LocalAppData%\Programs\Python\Python312\python.exe"
if not exist "%BOOTSTRAP_PYTHON%" goto setup_failed

:create_runtime
"%BOOTSTRAP_PYTHON%" setup_runtime.py
if errorlevel 1 goto setup_failed
goto launch

:ensure_runtime
"%VENV_PYTHON%" setup_runtime.py
if errorlevel 1 goto setup_failed

:launch
set "PATH=%CD%\.venv\Scripts;%LocalAppData%\Microsoft\WinGet\Links;%PATH%"
if not exist "%VENV_PYTHONW%" goto setup_failed
start "" "%VENV_PYTHONW%" main.py
exit /b 0

:setup_failed
echo.
echo StemPy runtime setup failed. Check the error above and try again.
pause
exit /b 1
