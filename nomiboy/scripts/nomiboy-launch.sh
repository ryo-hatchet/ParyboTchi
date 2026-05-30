#!/usr/bin/env bash
# Pi 上で nomiboy を Wayland セッション内に立ち上げるラッパー。
# Desktop ランチャーや手動起動から呼ぶ想定。
#
# 動作:
# 1. ALSA を占有している audio-idle-suppressor を一時停止
# 2. systemd-run --user で nomiboy を transient unit として起動
# 3. （nomiboy を止めた後の audio-idle-suppressor 復旧はユーザー操作で）
set -euo pipefail

NOMIBOY_DIR="${NOMIBOY_DIR:-$HOME/ParyboTchi/nomiboy}"
# 既存のシステム unit (install_pi.sh の nomiboy.service) と名前衝突しないよう -app を付ける
UNIT_NAME="${NOMIBOY_UNIT:-nomiboy-app}"

export XDG_RUNTIME_DIR="/run/user/$(id -u)"

# 既に起動中なら何もしない
if systemctl --user is-active --quiet "${UNIT_NAME}.service"; then
  notify-send -t 2000 "nomiboy" "すでに起動中" 2>/dev/null || true
  exit 0
fi

# ALSA を占有している音入れっぱなしサービスを止める（存在すれば）
if systemctl --user list-unit-files 2>/dev/null | grep -q '^audio-idle-suppressor\.service'; then
  systemctl --user kill -s KILL audio-idle-suppressor 2>/dev/null || true
fi
pkill -9 -x aplay 2>/dev/null || true

# nomiboy を起動（labwc セッションの環境を継承）
# パネルが NOT 反転しない構成では NOMIBOY_INVERT_COLORS は付けない
systemd-run --user --no-block --unit="${UNIT_NAME}" \
  -p Environment=PYTHONPATH=src \
  -p Environment=DISPLAY="${DISPLAY:-:0}" \
  -p Environment=WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}" \
  -p Environment=XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR}" \
  --working-directory="${NOMIBOY_DIR}" \
  "${NOMIBOY_DIR}/venv/bin/python" -m nomiboy --windowed

notify-send -t 2000 "nomiboy" "起動しました" 2>/dev/null || true
