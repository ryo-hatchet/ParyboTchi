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
        self._bg: pygame.Surface | None = None
        self._t: float = 0.0

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 24), colors.INK_LIGHT
        )
        self._t = 0.0
        # 背景画像をアスペクト保ったままロード
        from nomiboy.core.widgets.bg import load_background
        self._bg = load_background(ctx, "images/background.png", config.SCREEN_SIZE)
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
        if self._bg is not None:
            surface.blit(self._bg, (0, 0))
        else:
            surface.fill(colors.BG_PRIMARY)
        # 文字の視認性確保のため半透明オーバーレイ
        overlay = pygame.Surface(config.SCREEN_SIZE, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))
        cx = config.SCREEN_SIZE[0] // 2
        self._title_r.draw(surface, "どのゲームで", (cx, 130), anchor="center")
        self._title_r.draw(surface, "乾杯する？", (cx, 175), anchor="center")
