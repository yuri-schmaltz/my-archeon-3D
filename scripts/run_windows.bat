@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for %%I in ("%SCRIPT_DIR%\..") do set "ROOT_DIR=%%~fI"
set "VENV_DIR=%ROOT_DIR%\.venv"

if not exist "%VENV_DIR%" (
    echo ERROR: Virtual environment not found.
    echo Please run install_windows.bat first.
    pause
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
set "PYTHONPATH=%ROOT_DIR%;%PYTHONPATH%"

echo === Starting Archeon 3D ===
python "%ROOT_DIR%\archeon_3d.py"

if %errorlevel% neq 0 (
    echo.
    echo App crashed or closed with error. Check logs above.
    pause
)
