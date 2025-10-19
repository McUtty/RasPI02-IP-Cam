#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
CERT_FILE="${CERT_FILE:-cert.pem}"
KEY_FILE="${KEY_FILE:-key.pem}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8443}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Fehler: Python-Interpreter '$PYTHON_BIN' nicht gefunden." >&2
  exit 1
fi

if [[ ! -f "$CERT_FILE" ]]; then
  echo "Fehler: Zertifikatsdatei '$CERT_FILE' wurde nicht gefunden." >&2
  exit 1
fi

if [[ ! -f "$KEY_FILE" ]]; then
  echo "Fehler: Schlüsseldatei '$KEY_FILE' wurde nicht gefunden." >&2
  exit 1
fi

exec "$PYTHON_BIN" IPcam.py \
  --cert "$CERT_FILE" \
  --key "$KEY_FILE" \
  --host "$HOST" \
  --port "$PORT"
