"""ゲーム選択画面。`games/__init__.py` の GAME_META 一覧を表示。"""
from __future__ import annotations

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer


class GameSelectScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._buttons: list[Button] = []
        self._title_r: TextRenderer | None = None
        self._btn_r: TextRenderer | None = None
        self._ctx: AppContext | None = None

    def on_enter(self, ctx: AppContext) -> None:
        from nomiboy.games import GAME_META  # 遅延 import
        self._ctx = ctx
        self._title_r = TextRenderer(ctx.assets.font("DotGothic16-Regular.ttf", 18), colors.INK_DARK)
        self._btn_r = TextRenderer(ctx.assets.font("DotGothic16-Regular.ttf", 12), colors.INK_DARK)
        self._buttons = []
        bw, bh = 130, 130
        gap = (config.SCREEN_SIZE[0] - bw * 3) // 4
        y = 90
        for i, meta in enumerate(GAME_META):
            x = gap + i * (bw + gap)
            self._buttons.append(Button(
                rect=pygame.Rect(x, y, bw, bh),
                label=meta.title,
                on_tap=lambda key=meta.key: self._launch(key),
                bg_color=colors.player_color(i),
            ))
        self._buttons.append(Button(
            rect=pygame.Rect(10, 10, 100, 26),
            label="TITLE",
            on_tap=self._reset_to_title,
            bg_color=colors.ACCENT_BERRY,
            fg_color=colors.INK_LIGHT,
        ))

    def on_exit(self) -> None:
        pass

    def _launch(self, key: str) -> None:
        if key == "bomb":
            from nomiboy.games.bomb import BombScene
            self._sm.push(BombScene(self._sm))
        elif key == "roulette":
            from nomiboy.games.roulette import RouletteScene
            self._sm.push(RouletteScene(self._sm))
        elif key == "odai":
            from nomiboy.games.odai import OdaiScene
            self._sm.push(OdaiScene(self._sm))

    def _reset_to_title(self) -> None:
        from nomiboy.scenes.title import TitleScene
        self._ctx.players.clear()
        self._sm.reset_to(TitleScene(self._sm))

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        self._title_r.draw(surface, "SELECT GAME", (config.SCREEN_SIZE[0] // 2, 50), anchor="center")
        for b in self._buttons:
            b.draw(surface, self._btn_r)
