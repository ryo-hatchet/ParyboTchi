"""python -m nomiboy のエントリーポイント。"""
from __future__ import annotations

import argparse
import logging
import os
import sys

# SDL に touch → mouse の自動変換を切らせる（1 タップが 2 回押下扱いになるのを回避）
# pygame import より前に設定する必要がある
os.environ.setdefault("SDL_TOUCH_MOUSE_EVENTS", "0")
os.environ.setdefault("SDL_MOUSE_TOUCH_EVENTS", "0")

from nomiboy.app import App  # noqa: E402
from nomiboy.config import LOG_DIR  # noqa: E402


def _setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "log.txt"),
            logging.StreamHandler(sys.stderr),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windowed", action="store_true", help="全画面を無効化（PCデバッグ用）")
    args = parser.parse_args()
    if args.windowed:
        os.environ["NOMIBOY_FULLSCREEN"] = "0"
    _setup_logging()
    App().run()


if __name__ == "__main__":
    main()
