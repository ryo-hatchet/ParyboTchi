"""画像・フォントの読み込みとキャッシュ。"""
from __future__ import annotations

from pathlib import Path

import pygame

from nomiboy.config import ASSETS_DIR


class AssetLoader:
    def __init__(self, base_dir: Path = ASSETS_DIR) -> None:
        self._base = base_dir
        self._image_cache: dict[Path, pygame.Surface] = {}
        self._font_cache: dict[tuple[str, int], pygame.font.Font] = {}

    def image(self, relative_path: str) -> pygame.Surface:
        p = self._base / relative_path
        cached = self._image_cache.get(p)
        if cached is not None:
            return cached
        surf = pygame.image.load(str(p)).convert_alpha()
        self._image_cache[p] = surf
        return surf

    def font(self, name: str, size: int) -> pygame.font.Font:
        key = (name, size)
        cached = self._font_cache.get(key)
        if cached is not None:
            return cached
        font_path = self._base / "fonts" / name
        if font_path.exists():
            f = pygame.font.Font(str(font_path), size)
        else:
            f = pygame.font.Font(None, size)
        self._font_cache[key] = f
        return f
