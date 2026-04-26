#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source venv/bin/activate
PYTHONPATH=src exec python -m nomiboy --windowed
