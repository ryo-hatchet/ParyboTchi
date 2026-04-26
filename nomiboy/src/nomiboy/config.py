"""nomiboy 設定モジュール。

環境変数：
- NOMIBOY_FORCE_PI=1   ハード判定を強制的に Pi 扱い（再現テスト用）
- NOMIBOY_FULLSCREEN=0 全画面を無効化（PCデバッグ用）
"""
from __future__ import annotations

import os
from pathlib import Path

SCREEN_SIZE: tuple[int, int] = (480, 320)
TARGET_FPS: int = 30


def detect_is_pi() -> bool:
    if os.environ.get("NOMIBOY_FORCE_PI") == "1":
        return True
    model_file = Path("/sys/firmware/devicetree/base/model")
    if not model_file.exists():
        return False
    try:
        return "Raspberry Pi" in model_file.read_text(errors="ignore")
    except OSError:
        return False


def detect_fullscreen() -> bool:
    override = os.environ.get("NOMIBOY_FULLSCREEN")
    if override is not None:
        return override == "1"
    return detect_is_pi()


def detect_hide_cursor() -> bool:
    return detect_is_pi()


IS_PI = detect_is_pi()
FULLSCREEN = detect_fullscreen()
HIDE_CURSOR = detect_hide_cursor()

ROOT_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = ROOT_DIR / "assets"
DATA_DIR = ROOT_DIR / "data"
TTS_CACHE_DIR = ASSETS_DIR / "tts_cache"
LOG_DIR = Path.home() / ".nomiboy"
