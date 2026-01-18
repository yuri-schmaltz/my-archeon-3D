#!/bin/bash
set -e

echo "Building Archeon 3D for Linux..."

# Ensure we are in the root
if [ ! -f "archeon_3d.py" ]; then
    echo "Error: Please run this script from the project root."
    exit 1
fi

# Activate venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Warning: .venv not found. Assuming environment is ready."
fi

# Install PyInstaller if missing
pip install pyinstaller

# Run Build
pyinstaller build_scripts/archeon3d.spec --noconfirm --clean

echo "Build Complete! Executable is in dist/Archeon3D/Archeon3D"
