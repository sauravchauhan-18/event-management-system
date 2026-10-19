@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating the project environment...
    py -m venv .venv 2>nul
    if errorlevel 1 python -m venv .venv
    if errorlevel 1 (
        echo Could not create the Python environment. Install Python and try again.
        pause
        exit /b 1
    )
)

if not exist ".venv\Lib\site-packages\flask\__init__.py" (
    echo Installing project requirements...
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed.
        pause
        exit /b 1
    )
)

echo Starting Gather. Close this window to stop the app.
.venv\Scripts\python.exe app.py
pause
