"""タイトル画面。tap で PlayerRegisterScene へ。"""
from __future__ import annotations

import time

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.text import TextRenderer


class TitleScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._title_renderer: TextRenderer | None = None
        self._sub_renderer: TextRenderer | None = None
        self._offline_renderer: TextRenderer | None = None
        self._t0 = 0.0

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_renderer = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 36), colors.INK_DARK)
        self._sub_renderer = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 14), colors.INK_DARK)
        self._offline_renderer = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 10), colors.DANGER_RED)
        self._t0 = time.time()

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: InputEvent) -> None:
        if event.kind == InputKind.TAP:
            from nomiboy.scenes.player_register import PlayerRegisterScene
            self._sm.replace(PlayerRegisterScene(self._sm))

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        self._title_renderer.draw(surface, "NOMIBOY", (config.SCREEN_SIZE[0] // 2, 130), anchor="center")
        if int((time.time() - self._t0) * 2) % 2 == 0:
            self._sub_renderer.draw(surface, "TAP TO START", (config.SCREEN_SIZE[0] // 2, 220), anchor="center")
        if not self._ctx.online:
            self._offline_renderer.draw(surface, "OFFLINE", (config.SCREEN_SIZE[0] - 8, 8), anchor="topright")
