#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

python IPcam.py --cert cert.pem --key key.pem --host 0.0.0.0 --port 8443
