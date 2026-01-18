@echo off
SETLOCAL EnableDelayedExpansion

REM ============================================================================
REM Archeon 3D - Windows Build Script
REM ============================================================================

echo [INFO] Starting Windows Build for Archeon 3D...

REM 1. Check for Virtual Environment
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found in .venv
    echo [INFO] Please run "python -m venv .venv" first.
    exit /b 1
)

REM 2. Activate Virtual Environment
call .venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate virtual environment.
    exit /b 1
)
echo [INFO] Virtual Environment Activated.

REM 3. Install/Upgrade Build Dependencies
echo [INFO] Installing/Updating PyInstaller...
pip install --upgrade pyinstaller
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install PyInstaller.
    exit /b 1
)

REM 4. Clean previous builds
if exist "dist" (
    echo [INFO] Cleaning 'dist' directory...
    rmdir /s /q "dist"
)
if exist "build" (
    echo [INFO] Cleaning 'build' directory...
    rmdir /s /q "build"
)

REM 5. Run PyInstaller
echo [INFO] Running PyInstaller with archeon3d.spec...
pyinstaller --clean --noconfirm build_scripts/archeon3d.spec

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller build failed!
    exit /b 1
)

echo.
echo ============================================================================
echo [SUCCESS] Build Complete!
echo Executive found in: dist\archeon_3d\archeon_3d.exe
echo ============================================================================

pause
