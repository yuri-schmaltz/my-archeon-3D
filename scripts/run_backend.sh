#!/bin/bash
# run_backend.sh
# Activates the virtual environment and runs the Archeon 3D API server

# Navigate to the project root (assuming this script is running from a known relative location or CWD is set correctly by Tauri)
# Tauri shell command CWD is usually the project root if configured, or we need to find it.
# For this specific setup, we know the relative paths.

# Resolve the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Starting Archeon 3D Backend..."
echo "Project Root: $PROJECT_ROOT"

# Activate Venv
source "$PROJECT_ROOT/.venv/bin/activate"

# Set PYTHONPATH
export PYTHONPATH=$PROJECT_ROOT:.

# Run Server
# Using port 8081 as defined in the plan
python "$PROJECT_ROOT/hy3dgen/apps/api_server.py" --port 8081
