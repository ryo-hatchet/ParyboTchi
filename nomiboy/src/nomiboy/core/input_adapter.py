"""タッチイベントとマウスイベントを統一の InputEvent に変換。"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import pygame


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

    def translate(self, event: Any) -> InputEvent | None:
        et = getattr(event, "type", None)
        if et == pygame.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            x, y = event.pos
            return InputEvent(InputKind.TAP, int(x), int(y))
        if et == pygame.MOUSEBUTTONUP and getattr(event, "button", None) == 1:
            x, y = event.pos
            return InputEvent(InputKind.RELEASE, int(x), int(y))
        if et == pygame.MOUSEMOTION:
            buttons = getattr(event, "buttons", (0, 0, 0))
            if buttons[0]:
                x, y = event.pos
                return InputEvent(InputKind.DRAG, int(x), int(y))
            return None
        if et == pygame.FINGERDOWN:
            return InputEvent(InputKind.TAP, int(event.x * self._w), int(event.y * self._h))
        if et == pygame.FINGERUP:
            return InputEvent(InputKind.RELEASE, int(event.x * self._w), int(event.y * self._h))
        if et == pygame.FINGERMOTION:
            return InputEvent(InputKind.DRAG, int(event.x * self._w), int(event.y * self._h))
        return None
