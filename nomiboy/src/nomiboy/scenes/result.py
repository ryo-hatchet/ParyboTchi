"""結果発表画面。爆弾・ルーレットでハズレた人を表示。"""
from __future__ import annotations

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.text import TextRenderer
from nomiboy.stores.player_store import Player


class ResultScene:
    def __init__(self, scene_manager, loser: Player) -> None:
        self._sm = scene_manager
        self._loser = loser
        self._title_r: TextRenderer | None = None
        self._sub_r: TextRenderer | None = None

    def on_enter(self, ctx: AppContext) -> None:
        self._title_r = TextRenderer(ctx.assets.font("DotGothic16-Regular.ttf", 28), colors.INK_DARK)
        self._sub_r = TextRenderer(ctx.assets.font("DotGothic16-Regular.ttf", 12), colors.INK_DARK)
        if ctx.online:
            ctx.tts.speak(f"{self._loser.name} は飲む！")

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: InputEvent) -> None:
        if event.kind == InputKind.TAP:
            self._sm.pop()  # Result 抜ける
            self._sm.pop()  # 個別ゲームも抜ける（GameSelect に戻る）

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(self._loser.color)
        self._title_r.draw(surface, f"{self._loser.name}", (config.SCREEN_SIZE[0] // 2, 120), anchor="center", color=colors.INK_LIGHT)
        self._sub_r.draw(surface, "は 飲む！", (config.SCREEN_SIZE[0] // 2, 170), anchor="center", color=colors.INK_LIGHT)
        self._sub_r.draw(surface, "tap to continue", (config.SCREEN_SIZE[0] // 2, 280), anchor="center", color=colors.INK_LIGHT)
