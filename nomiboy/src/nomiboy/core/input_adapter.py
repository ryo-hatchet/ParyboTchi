"""タッチイベントとマウスイベントを統一の InputEvent に変換。"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import pygame

# Wayland 経由で同一タップが mouse + finger の両方として届くことがあるので
# 直近の TAP/RELEASE をこの ms 以内に再度受けても無視する
_DEDUPE_MS = 80


class InputKind(Enum):
    TAP = "tap"
    RELEASE = "release"
    DRAG = "drag"


@dataclass(frozen=True)
class InputEvent:
    kind: InputKind
    x: int
    y: int


class InputAdapter:
    def __init__(self, screen_size: tuple[int, int]) -> None:
        self._w, self._h = screen_size
        self._last_tap_ms: int = -10000
        self._last_release_ms: int = -10000

    def _maybe_tap(self, x: int, y: int) -> InputEvent | None:
        now = pygame.time.get_ticks()
        if now - self._last_tap_ms < _DEDUPE_MS:
            return None
        self._last_tap_ms = now
        return InputEvent(InputKind.TAP, x, y)

    def _maybe_release(self, x: int, y: int) -> InputEvent | None:
        now = pygame.time.get_ticks()
        if now - self._last_release_ms < _DEDUPE_MS:
            return None
        self._last_release_ms = now
        return InputEvent(InputKind.RELEASE, x, y)

    def translate(self, event: Any) -> InputEvent | None:
        et = getattr(event, "type", None)
        if et == pygame.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            x, y = event.pos
            return self._maybe_tap(int(x), int(y))
        if et == pygame.MOUSEBUTTONUP and getattr(event, "button", None) == 1:
            x, y = event.pos
            return self._maybe_release(int(x), int(y))
        if et == pygame.MOUSEMOTION:
            buttons = getattr(event, "buttons", (0, 0, 0))
            if buttons[0]:
                x, y = event.pos
                return InputEvent(InputKind.DRAG, int(x), int(y))
            return None
        if et == pygame.FINGERDOWN:
            return self._maybe_tap(int(event.x * self._w), int(event.y * self._h))
        if et == pygame.FINGERUP:
            return self._maybe_release(int(event.x * self._w), int(event.y * self._h))
        if et == pygame.FINGERMOTION:
            return InputEvent(InputKind.DRAG, int(event.x * self._w), int(event.y * self._h))
        return None
