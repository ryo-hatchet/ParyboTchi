"""ルーレットゲーム。"""
from __future__ import annotations

import random

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer


class RouletteController:
    def __init__(self, player_count: int, rng: random.Random | None = None) -> None:
        self._n = player_count
        self._rng = rng or random.Random()
        self._spinning = False
        self._selected: int = 0
        self._cursor: int = 0

    @property
    def is_spinning(self) -> bool:
        return self._spinning

    @property
    def selected_index(self) -> int:
        return self._selected

    @property
    def cursor(self) -> int:
        return self._cursor

    def start(self) -> None:
        self._spinning = True
        self._cursor = 0

    def advance_cursor(self) -> None:
        if self._spinning:
            self._cursor = (self._cursor + 1) % self._n

    def stop(self) -> None:
        if not self._spinning:
            return
        self._selected = self._rng.randrange(self._n)
        self._cursor = self._selected
        self._spinning = False


class RouletteScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._ctrl: RouletteController | None = None
        self._title_r: TextRenderer | None = None
        self._buttons: list[Button] = []
        self._next_tick: float = 0.0

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 18), colors.INK_DARK)
        self._ctrl = RouletteController(player_count=ctx.players.count)
        self._ctrl.start()
        self._buttons = [
            Button(pygame.Rect(10, 10, 80, 26), "BACK", self._sm.pop, bg_color=colors.ACCENT_BERRY, fg_color=colors.INK_LIGHT),
            Button(pygame.Rect(160, 240, 160, 60), "STOP", self._stop, bg_color=colors.BG_SECONDARY),
        ]

    def on_exit(self) -> None:
        pass

    def _stop(self) -> None:
        self._ctrl.stop()
        from nomiboy.scenes.result import ResultScene
        loser = self._ctx.players.players[self._ctrl.selected_index]
        self._sm.push(ResultScene(self._sm, loser))

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        if not self._ctrl.is_spinning:
            return
        self._next_tick -= dt
        if self._next_tick <= 0:
            self._ctrl.advance_cursor()
            self._next_tick = 0.1

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        for i, p in enumerate(self._ctx.players.players):
            highlight = (i == self._ctrl.cursor)
            color = p.color if highlight else colors.INK_LIGHT
            rect = pygame.Rect(40 + i * 100, 100, 80, 80)
            pygame.draw.rect(surface, color, rect)
            self._title_r.draw(surface, p.name, rect.center, anchor="center", color=colors.INK_DARK)
        for b in self._buttons:
            b.draw(surface, self._title_r)
