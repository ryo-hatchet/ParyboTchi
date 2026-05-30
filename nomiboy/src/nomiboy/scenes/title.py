"""タイトル画面。tap で PlayerRegisterScene へ。"""
from __future__ import annotations

import time

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.text import TextRenderer


class TitleScene:
    show_menu = False

    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._offline_renderer: TextRenderer | None = None
        self._bg: pygame.Surface | None = None
        self._t0 = 0.0

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._offline_renderer = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 10), colors.DANGER_RED
        )
        # 背景画像をロード & 画面サイズへ縮小（一度だけ）
        raw = ctx.assets.image("images/title_bg.png")
        scaled = pygame.transform.smoothscale(raw, config.SCREEN_SIZE)
        # パネルが全色 NOT 反転する環境では画像も予め反転して打ち消す
        if colors.INVERT_COLORS:
            inv = pygame.Surface(scaled.get_size())
            inv.fill((255, 255, 255))
            inv.blit(scaled, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
            scaled = inv
        self._bg = scaled
        self._t0 = time.time()
        ctx.audio.play_bgm("title.mp3")

    def on_exit(self) -> None:
        # BGM は PlayerRegister でも継続させたいのでここでは停止しない
        pass

    def handle_event(self, event: InputEvent) -> None:
        if event.kind == InputKind.TAP:
            if self._ctx is not None:
                self._ctx.audio.play_se("start.wav")
            from nomiboy.scenes.player_register import PlayerRegisterScene
            self._sm.replace(PlayerRegisterScene(self._sm))

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        if self._bg is not None:
            surface.blit(self._bg, (0, 0))
        else:
            surface.fill(colors.BG_PRIMARY)
        if not self._ctx.online:
            self._offline_renderer.draw(
                surface, "OFFLINE", (config.SCREEN_SIZE[0] - 8, 8), anchor="topright"
            )
