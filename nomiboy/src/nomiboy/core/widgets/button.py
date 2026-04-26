"""タッチ可能なボタン。InputEvent.TAP の hit-test を提供。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pygame

from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.text import TextRenderer


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    on_tap: Callable[[], None]
    bg_color: tuple[int, int, int] = (255, 203, 5)
    fg_color: tuple[int, int, int] = (43, 10, 61)
    border_color: tuple[int, int, int] = (43, 10, 61)
    enabled: bool = True

    def hit(self, event: InputEvent) -> bool:
        if not self.enabled:
            return False
        if event.kind != InputKind.TAP:
            return False
        return self.rect.collidepoint(event.x, event.y)

    def handle(self, event: InputEvent) -> bool:
        if self.hit(event):
            self.on_tap()
            return True
        return False

    def draw(self, surface: pygame.Surface, text_renderer: TextRenderer) -> None:
        color = self.bg_color if self.enabled else (160, 160, 160)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, width=2)
        text_renderer.draw(surface, self.label, self.rect.center, anchor="center", color=self.fg_color)
