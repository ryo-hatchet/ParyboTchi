"""仮想キーボード画面。確定で前画面に戻り、コールバックで名前を渡す。"""
from __future__ import annotations

from typing import Callable

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.keyboard import VirtualKeyboard
from nomiboy.core.widgets.text import TextRenderer


class KeyboardInputScene:
    def __init__(self, scene_manager, on_confirm: Callable[[str], None]) -> None:
        self._sm = scene_manager
        self._on_confirm = on_confirm
        self._ctx: AppContext | None = None
        self._kb = VirtualKeyboard(area=(10, 80, 460, 200), max_len=8)
        self._buttons: list[Button] = []
        self._char_rects: list[tuple[pygame.Rect, str]] = []
        self._text_r: TextRenderer | None = None
        self._char_r: TextRenderer | None = None

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._text_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 18), colors.INK_DARK)
        self._char_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 14), colors.INK_DARK)
        self._buttons = [
            Button(pygame.Rect(10, 290, 100, 24), "MODE", self._switch_mode, bg_color=colors.ACCENT_BERRY, fg_color=colors.INK_LIGHT),
            Button(pygame.Rect(120, 290, 80, 24), "BS", self._kb.backspace, bg_color=colors.WARNING_AMBER),
            Button(pygame.Rect(210, 290, 80, 24), "CLR", self._kb.clear, bg_color=colors.WARNING_AMBER),
            Button(pygame.Rect(370, 290, 100, 24), "OK", self._confirm, bg_color=colors.BG_SECONDARY),
            Button(pygame.Rect(10, 10, 60, 24), "BACK", self._sm.pop, bg_color=colors.ACCENT_BERRY, fg_color=colors.INK_LIGHT),
        ]
        self._build_grid()

    def on_exit(self) -> None:
        pass

    def _switch_mode(self) -> None:
        self._kb.switch_mode()
        self._build_grid()

    def _build_grid(self) -> None:
        self._char_rects = []
        x0, y0, w, h = self._kb.area
        rows = self._kb.rows()
        rh = h // max(1, len(rows))
        for ri, row in enumerate(rows):
            cw = w // max(1, len(row))
            for ci, ch in enumerate(row):
                r = pygame.Rect(x0 + ci * cw, y0 + ri * rh, cw - 2, rh - 2)
                self._char_rects.append((r, ch))

    def _confirm(self) -> None:
        if not self._kb.text:
            return
        self._on_confirm(self._kb.text)
        self._sm.pop()

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                return
        if event.kind == InputKind.TAP:
            for r, ch in self._char_rects:
                if r.collidepoint(event.x, event.y):
                    self._kb.append(ch)
                    return

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        self._text_r.draw(surface, self._kb.text or "_", (config.SCREEN_SIZE[0] // 2, 50), anchor="center")
        for r, ch in self._char_rects:
            pygame.draw.rect(surface, colors.INK_LIGHT, r)
            pygame.draw.rect(surface, colors.INK_DARK, r, width=1)
            self._char_r.draw(surface, ch, r.center, anchor="center")
        for b in self._buttons:
            b.draw(surface, self._char_r)
