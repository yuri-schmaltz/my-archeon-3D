#!/bin/bash
set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
ROOT_DIR=$(dirname "$SCRIPT_DIR")
ICON_PATH="$ROOT_DIR/app/src-tauri/icons/icon.png"
EXEC_PATH="$ROOT_DIR/scripts/run_linux.sh"

DESKTOP_FILE="$HOME/.local/share/applications/archeon-3d.desktop"

echo "Creating desktop entry at $DESKTOP_FILE..."

# Ensure directory exists
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=Archeon 3D
Comment=Unified 3D Generation System
Exec="$EXEC_PATH"
Icon="$ICON_PATH"
Terminal=true
Type=Application
Categories=Graphics;Science;AI;
EOF

chmod +x "$DESKTOP_FILE"

echo "Shortcut created! You may need to log out and back in, or refresh GNOME."
