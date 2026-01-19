#!/bin/bash
set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
ROOT_DIR=$(dirname "$SCRIPT_DIR")
VENV_DIR="$ROOT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: Virtual environment not found at $VENV_DIR."
    echo "Please run ./scripts/install_linux.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"

# Set PYTHONPATH to project root just in case
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"

echo "=== Starting Archeon 3D ==="
python3 "$ROOT_DIR/archeon_3d.py"
