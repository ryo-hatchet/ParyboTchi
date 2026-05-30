#!/usr/bin/env bash
# Raspberry Pi のデスクトップに nomiboy 起動アイコンを設置する。
# Pi 上で `bash scripts/install_desktop_icon.sh` を実行する想定。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP_DIR="$HOME/Desktop"
APP_LOCAL_DIR="$HOME/.local/share/applications"

mkdir -p "$DESKTOP_DIR" "$APP_LOCAL_DIR"

# 起動スクリプトに実行権限
chmod +x "$ROOT/scripts/nomiboy-launch.sh"

# .desktop ファイル内の Exec / Path をこの環境に合わせて書き換えてコピー
DESKTOP_SRC="$ROOT/scripts/nomiboy.desktop"
DESKTOP_DST="$DESKTOP_DIR/nomiboy.desktop"

sed -e "s|^Exec=.*|Exec=$ROOT/scripts/nomiboy-launch.sh|" \
    "$DESKTOP_SRC" > "$DESKTOP_DST"

chmod +x "$DESKTOP_DST"

# PCManFM / labwc-desktop で「信頼済み」と扱わせる
if command -v gio >/dev/null 2>&1; then
  gio set "$DESKTOP_DST" metadata::trusted true || true
fi

# アプリケーションメニューにも登録
cp -f "$DESKTOP_DST" "$APP_LOCAL_DIR/nomiboy.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_LOCAL_DIR" >/dev/null 2>&1 || true
fi

echo "Installed:"
echo "  $DESKTOP_DST"
echo "  $APP_LOCAL_DIR/nomiboy.desktop"
echo ""
echo "デスクトップを更新したら、初回は右クリック → 「実行を許可」 / 「信頼する」 が必要な場合があります。"
