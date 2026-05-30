"""プレイヤー登録完了直後の橋渡し画面。

「どのゲームで乾杯する？」を 2 秒表示してから GameSelect に自動遷移する。
背景でドリンクコール曲が生成されている間の繋ぎでもある。
"""
from __future__ import annotations

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.widgets.text import TextRenderer


_DURATION_SEC = 2.0


class GameSelectIntroScene:
    show_menu = False

    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._title_r: TextRenderer | None = None
        self._t: float = 0.0

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 24), colors.INK_DARK
        )
        self._t = 0.0
        # タイトル BGM をここで終了
        ctx.audio.stop_bgm()

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: InputEvent) -> None:
        # スプラッシュ中はタップを無視
        pass

    def update(self, dt: float) -> None:
        self._t += dt
        if self._t >= _DURATION_SEC:
            from nomiboy.scenes.game_select import GameSelectScene

            self._sm.replace(GameSelectScene(self._sm))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        cx = config.SCREEN_SIZE[0] // 2
        self._title_r.draw(surface, "どのゲームで", (cx, 130), anchor="center")
        self._title_r.draw(surface, "乾杯する？", (cx, 175), anchor="center")
