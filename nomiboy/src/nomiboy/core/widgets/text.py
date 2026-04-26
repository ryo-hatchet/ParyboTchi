"""テキスト描画ヘルパ。フォントサーフェスをキャッシュ。"""
from __future__ import annotations

import pygame


class TextRenderer:
    def __init__(self, font: pygame.font.Font, color: tuple[int, int, int]) -> None:
        self._font = font
        self._color = color
        self._cache: dict[tuple[str, tuple[int, int, int]], pygame.Surface] = {}

    def render(self, text: str, color: tuple[int, int, int] | None = None) -> pygame.Surface:
        c = color or self._color
        key = (text, c)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        surf = self._font.render(text, True, c)
        self._cache[key] = surf
        return surf

    def draw(
        self,
        surface: pygame.Surface,
        text: str,
        pos: tuple[int, int],
        anchor: str = "topleft",
        color: tuple[int, int, int] | None = None,
    ) -> pygame.Rect:
        s = self.render(text, color)
        rect = s.get_rect(**{anchor: pos})
        surface.blit(s, rect)
        return rect
