#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

VENV_DIR="${VENV_DIR:-.venv}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
BROWSER_HOST="${BROWSER_HOST:-127.0.0.1}"

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "V2 is not installed yet. Run: bash install_v2.sh" >&2
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

export CHATBOT_RECEPTION_TOKEN="${CHATBOT_RECEPTION_TOKEN:-demo-reception-token}"
export CHATBOT_HOUSEKEEPING_TOKEN="${CHATBOT_HOUSEKEEPING_TOKEN:-demo-housekeeping-token}"
export CHATBOT_MANAGER_TOKEN="${CHATBOT_MANAGER_TOKEN:-demo-manager-token}"

URL="http://${BROWSER_HOST}:${PORT}/app/"

echo
echo "Hotel PMS Chatbot V2"
echo "Web app: $URL"
echo "API docs: http://${BROWSER_HOST}:${PORT}/docs"
echo "Press Ctrl+C to stop."
echo

python -m uvicorn main:app --host "$HOST" --port "$PORT" &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if command -v xdg-open >/dev/null 2>&1; then
  (
    sleep 1
    xdg-open "$URL" >/dev/null 2>&1 || true
  ) &
fi

wait "$SERVER_PID"
