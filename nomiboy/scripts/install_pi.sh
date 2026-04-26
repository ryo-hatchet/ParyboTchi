#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)

if [ ! -d venv ]; then
  python3.11 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

sudo cp scripts/nomiboy.service /etc/systemd/system/nomiboy.service
sudo systemctl daemon-reload
sudo systemctl enable nomiboy
echo "Installed. Reboot or run: sudo systemctl start nomiboy"
