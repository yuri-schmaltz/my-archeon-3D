@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for %%I in ("%SCRIPT_DIR%\..") do set "ROOT_DIR=%%~fI"

set "TARGET=%SCRIPT_DIR%\run_windows.bat"
set "ICON=%ROOT_DIR%\app\src-tauri\icons\icon.ico"
set "SHORTCUT=%USERPROFILE%\Desktop\Archeon 3D.lnk"

echo Creating shortcut on Desktop...
echo Target: %TARGET%
echo Icon: %ICON%

powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%');$s.TargetPath='%TARGET%';$s.IconLocation='%ICON%';$s.WorkingDirectory='%ROOT_DIR%';$s.Save()"

if %errorlevel% equ 0 (
    echo Shortcut created successfully!
) else (
    echo Failed to create shortcut.
)
pause
