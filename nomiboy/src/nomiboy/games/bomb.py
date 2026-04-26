"""爆弾タイマーゲーム。コントローラ（純ロジック）と Scene を分離。"""
from __future__ import annotations

import random
import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer


class BombController:
    def __init__(
        self,
        player_count: int,
        rng: random.Random | None = None,
        min_sec: float = 10.0,
        max_sec: float = 30.0,
    ) -> None:
        self._n = player_count
        self._rng = rng or random.Random()
        self._min = min_sec
        self._max = max_sec
        self._remaining: float = 0.0
        self._holder: int = 0
        self._started: bool = False

    @property
    def remaining(self) -> float:
        return self._remaining

    @property
    def holder(self) -> int:
        return self._holder

    @property
    def exploded(self) -> bool:
        return self._started and self._remaining <= 0.0

    def start(self) -> None:
        self._remaining = self._rng.uniform(self._min, self._max)
        self._holder = 0
        self._started = True

    def pass_to_next(self) -> None:
        if not self._started or self.exploded:
            return
        self._holder = (self._holder + 1) % self._n

    def tick(self, dt: float) -> None:
        if not self._started or self.exploded:
            return
        self._remaining = max(0.0, self._remaining - dt)


class BombScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._ctrl: BombController | None = None
        self._title_r: TextRenderer | None = None
        self._buttons: list[Button] = []
        self._exploded_handled = False

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 18), colors.INK_DARK)
        self._ctrl = BombController(player_count=ctx.players.count)
        self._ctrl.start()
        self._exploded_handled = False
        self._buttons = [
            Button(pygame.Rect(10, 10, 80, 26), "BACK", self._sm.pop, bg_color=colors.ACCENT_BERRY, fg_color=colors.INK_LIGHT),
            Button(pygame.Rect(160, 240, 160, 60), "PASS", self._ctrl.pass_to_next, bg_color=colors.BG_SECONDARY),
        ]

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        self._ctrl.tick(dt)
        if self._ctrl.exploded and not self._exploded_handled:
            self._exploded_handled = True
            from nomiboy.scenes.result import ResultScene
            loser = self._ctx.players.players[self._ctrl.holder]
            self._sm.push(ResultScene(self._sm, loser))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        if self._ctx and self._ctx.players.count > 0:
            holder_player = self._ctx.players.players[self._ctrl.holder]
            self._title_r.draw(surface, f"BOMB: {holder_player.name}", (config.SCREEN_SIZE[0] // 2, 90), anchor="center")
        self._title_r.draw(surface, f"{self._ctrl.remaining:.1f}s", (config.SCREEN_SIZE[0] // 2, 160), anchor="center", color=colors.DANGER_RED)
        for b in self._buttons:
            b.draw(surface, self._title_r)
