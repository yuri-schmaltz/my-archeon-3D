@echo off
setlocal
echo === Archeon 3D Installer (Windows) ===

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org and tick "Add Python to PATH".
    pause
    exit /b 1
)

:: Resolve paths
set "SCRIPT_DIR=%~dp0"
:: Removing trailing backslash if present
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for %%I in ("%SCRIPT_DIR%\..") do set "ROOT_DIR=%%~fI"
set "VENV_DIR=%ROOT_DIR%\.venv"

echo Project Root: "%ROOT_DIR%"

if exist "%VENV_DIR%" (
    echo Virtual environment already exists.
) else (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

:: Activate venv
call "%VENV_DIR%\Scripts\activate.bat"

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
pip install -r "%ROOT_DIR%\requirements.txt"

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo === Installation Complete! ===
echo You can run the app using scripts\run_windows.bat
pause
