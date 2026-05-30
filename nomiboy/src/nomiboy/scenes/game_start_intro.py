"""ゲーム開始直前のスプラッシュ画面。

「飲みゲーSTART！」とビールジョッキを 1.5 秒表示してから
指定されたゲームシーンに自動遷移する。
"""
from __future__ import annotations

from typing import Callable

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.widgets.text import TextRenderer


_DURATION_SEC = 1.5


class GameStartIntroScene:
    show_menu = False

    def __init__(
        self,
        scene_manager,
        next_scene_factory: Callable[[object], object],
    ) -> None:
        self._sm = scene_manager
        self._next_scene_factory = next_scene_factory
        self._ctx: AppContext | None = None
        self._title_r: TextRenderer | None = None
        self._t: float = 0.0

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 28), colors.INK_DARK
        )
        self._t = 0.0

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: InputEvent) -> None:
        # スプラッシュ中はタップを無視
        pass

    def update(self, dt: float) -> None:
        self._t += dt
        if self._t >= _DURATION_SEC:
            self._sm.replace(self._next_scene_factory(self._sm))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        cx = config.SCREEN_SIZE[0] // 2
        cy = config.SCREEN_SIZE[1] // 2
        self._title_r.draw(surface, "飲みゲーSTART！", (cx, cy - 50), anchor="center")
        _draw_beer_mug(surface, cx, cy + 50, size=80)


def _draw_beer_mug(surface: pygame.Surface, cx: int, cy: int, size: int = 80) -> None:
    """簡易ビールジョッキを描画。"""
    body_w = size
    body_h = int(size * 1.1)
    body = pygame.Rect(cx - body_w // 2, cy - body_h // 2, body_w, body_h)
    # ビール本体（黄金）
    pygame.draw.rect(surface, (240, 195, 50), body)
    pygame.draw.rect(surface, colors.INK_DARK, body, width=3)
    # 泡（白いカプセル）
    foam_h = int(size * 0.35)
    foam = pygame.Rect(body.left - 6, body.top - foam_h // 2, body_w + 12, foam_h)
    pygame.draw.ellipse(surface, (255, 255, 255), foam)
    pygame.draw.ellipse(surface, colors.INK_DARK, foam, width=3)
    # 取っ手（右側にコの字）
    handle = pygame.Rect(body.right - 2, body.top + body_h // 5, body_w // 3, int(body_h * 0.6))
    pygame.draw.rect(surface, (240, 195, 50), handle)
    pygame.draw.rect(surface, colors.INK_DARK, handle, width=3)
    # 取っ手の内側を背景色で塗りつぶす（穴っぽく見せる）
    inner = pygame.Rect(handle.left + 6, handle.top + 6, handle.width - 12, handle.height - 12)
    if inner.width > 0 and inner.height > 0:
        pygame.draw.rect(surface, colors.BG_PRIMARY, inner)
        pygame.draw.rect(surface, colors.INK_DARK, inner, width=2)
