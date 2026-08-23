#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

VENV_DIR="${VENV_DIR:-.venv}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
BROWSER_HOST="${BROWSER_HOST:-127.0.0.1}"
ALLOW_INSECURE_NETWORK_DEMO="${ALLOW_INSECURE_NETWORK_DEMO:-0}"

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "V2 is not installed yet. Run: bash install_v2.sh" >&2
  exit 1
fi

case "$HOST" in
  127.0.0.1|localhost|::1) ;;
  *)
    if [ "$ALLOW_INSECURE_NETWORK_DEMO" != "1" ]; then
      echo "Refusing non-loopback bind ('$HOST') with demo authentication." >&2
      echo "Use HOST=127.0.0.1 for local use, or explicitly set ALLOW_INSECURE_NETWORK_DEMO=1 after configuring a real network-safe authentication setup." >&2
      exit 1
    fi
    echo "WARNING: network demo mode is enabled; the built-in demo bearer tokens are not suitable for untrusted networks." >&2
    ;;
esac

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
