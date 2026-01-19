#!/bin/bash
set -e

echo "=== Archeon 3D Installer (Linux) ==="
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 could not be found. Please install Python 3 (sudo apt install python3 python3-venv)."
    exit 1
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
ROOT_DIR=$(dirname "$SCRIPT_DIR")
VENV_DIR="$ROOT_DIR/.venv"

echo "Project Root: $ROOT_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies from requirements.txt..."
pip install -r "$ROOT_DIR/requirements.txt"

echo "=== Installation Complete! ==="
echo "You can now run the app using ./scripts/run_linux.sh"
read -p "Press Enter to exit..."
