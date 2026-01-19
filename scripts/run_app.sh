#!/bin/bash
# run_app.sh - Archeon 3D Launcher

# Resolve the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Starting Archeon 3D Gradio Interface..."

# Activate Venv
source "$PROJECT_ROOT/.venv/bin/activate"

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/hy3dgen/texgen/custom_rasterizer:$PYTHONPATH"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Run Server
python "$PROJECT_ROOT/archeon_3d.py" "$@"
