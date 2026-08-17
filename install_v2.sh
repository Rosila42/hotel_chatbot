#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python executable '$PYTHON_BIN' was not found. Install Python 3.11+ first." >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment in $VENV_DIR..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements-v2.txt

chmod +x run_v2.sh verify_v2.sh install_v2.sh

# Install a user-level desktop launcher. No sudo is required.
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$APP_DIR"
DESKTOP_FILE="$APP_DIR/hotel-chatbot-v2.desktop"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Hotel Chatbot V2
Comment=Local Hotel PMS Chatbot
Exec=$ROOT/run_v2.sh
Path=$ROOT
Terminal=true
Categories=Office;Utility;
StartupNotify=true
EOF

chmod 644 "$DESKTOP_FILE"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
fi

echo
echo "Installation complete."
echo "You can now launch 'Hotel Chatbot V2' from the Ubuntu application menu."
echo "Or run: $ROOT/run_v2.sh"
