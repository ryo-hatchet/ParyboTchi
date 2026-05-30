"""ゲーム選択画面。`games/__init__.py` の GAME_META 一覧を 2×2 ページングで表示。"""
from __future__ import annotations

import math

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer
from nomiboy.games import GAME_META, GameMeta


# レイアウト定数
_PAGE_SIZE = 4  # 1ページ最大4ゲーム（2×2）
_BTN_W = 130
_BTN_H = 100
_GAP_X = 30
_GAP_Y = 12
_GRID_LEFT = (config.SCREEN_SIZE[0] - _BTN_W * 2 - _GAP_X) // 2  # 95
_GRID_TOP = 60
_NAV_W = 30
_NAV_H = 30
_NAV_Y = 280
_NAV_PREV_X = 395
_NAV_NEXT_X = 440
_DOT_SIZE = 8
_DOT_GAP = 10
_DOT_Y = 295


class GameSelectScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._title_r: TextRenderer | None = None
        self._btn_r: TextRenderer | None = None
        self._ctx: AppContext | None = None
        self._game_meta: list[GameMeta] = []
        self._game_buttons: list[Button] = []
        self._nav_buttons: list[Button] = []
        self._title_buttons: list[Button] = []
        self._current_page: int = 0
        self._total_pages: int = 1

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 18), colors.INK_DARK
        )
        self._btn_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 12), colors.INK_DARK
        )
        self._game_meta = list(GAME_META)
        self._total_pages = max(1, math.ceil(len(self._game_meta) / _PAGE_SIZE))
        self._current_page = 0
        self._title_buttons = [
            Button(
                rect=pygame.Rect(10, 10, 100, 26),
                label="TITLE",
                on_tap=self._reset_to_title,
                bg_color=colors.ACCENT_BERRY,
                fg_color=colors.INK_LIGHT,
            ),
        ]
        self._build_nav_buttons()
        self._rebuild_game_buttons()

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: InputEvent) -> None:
        for b in self._title_buttons:
            if b.handle(event):
                return
        for b in self._nav_buttons:
            if b.handle(event):
                return
        for b in self._game_buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        self._title_r.draw(
            surface, "SELECT GAME", (config.SCREEN_SIZE[0] // 2, 40), anchor="center"
        )
        for b in self._game_buttons:
            b.draw(surface, self._btn_r)
        for b in self._title_buttons:
            b.draw(surface, self._btn_r)
        for b in self._nav_buttons:
            b.draw(surface, self._btn_r)
        self._draw_page_indicator(surface)

    # ─────────── 内部 ───────────

    def _build_nav_buttons(self) -> None:
        if self._total_pages <= 1:
            self._nav_buttons = []
            return
        self._nav_buttons = [
            Button(
                rect=pygame.Rect(_NAV_PREV_X, _NAV_Y, _NAV_W, _NAV_H),
                label="<",
                on_tap=self._prev_page,
                bg_color=colors.ACCENT_BERRY,
                fg_color=colors.INK_LIGHT,
            ),
            Button(
                rect=pygame.Rect(_NAV_NEXT_X, _NAV_Y, _NAV_W, _NAV_H),
                label=">",
                on_tap=self._next_page,
                bg_color=colors.ACCENT_BERRY,
                fg_color=colors.INK_LIGHT,
            ),
        ]
        self._update_nav_enabled()

    def _update_nav_enabled(self) -> None:
        if not self._nav_buttons:
            return
        self._nav_buttons[0].enabled = self._current_page > 0
        self._nav_buttons[1].enabled = self._current_page < self._total_pages - 1

    def _rebuild_game_buttons(self) -> None:
        self._game_buttons = []
        page_start = self._current_page * _PAGE_SIZE
        page_end = min(page_start + _PAGE_SIZE, len(self._game_meta))
        for slot, idx in enumerate(range(page_start, page_end)):
            meta = self._game_meta[idx]
            row = slot // 2
            col = slot % 2
            x = _GRID_LEFT + col * (_BTN_W + _GAP_X)
            y = _GRID_TOP + row * (_BTN_H + _GAP_Y)
            self._game_buttons.append(
                Button(
                    rect=pygame.Rect(x, y, _BTN_W, _BTN_H),
                    label=meta.title,
                    on_tap=lambda key=meta.key: self._launch(key),
                    bg_color=colors.player_color(idx),
                )
            )

    def _draw_page_indicator(self, surface: pygame.Surface) -> None:
        if self._total_pages <= 1:
            return
        total_w = self._total_pages * _DOT_SIZE + (self._total_pages - 1) * _DOT_GAP
        left = (config.SCREEN_SIZE[0] - total_w) // 2
        for i in range(self._total_pages):
            x = left + i * (_DOT_SIZE + _DOT_GAP)
            rect = pygame.Rect(x, _DOT_Y, _DOT_SIZE, _DOT_SIZE)
            if i == self._current_page:
                pygame.draw.rect(surface, colors.INK_DARK, rect)
            else:
                pygame.draw.rect(surface, colors.INK_DARK, rect, width=1)

    def _prev_page(self) -> None:
        if self._current_page > 0:
            self._current_page -= 1
            self._rebuild_game_buttons()
            self._update_nav_enabled()

    def _next_page(self) -> None:
        if self._current_page < self._total_pages - 1:
            self._current_page += 1
            self._rebuild_game_buttons()
            self._update_nav_enabled()

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
        elif key == "russian_tap":
            from nomiboy.games.russian_tap import RussianTapScene

            self._sm.push(RussianTapScene(self._sm))

    def _reset_to_title(self) -> None:
        from nomiboy.scenes.title import TitleScene

        self._ctx.players.clear()
        self._sm.reset_to(TitleScene(self._sm))

    # ─────────── テスト用フック（read-only） ───────────

    @property
    def current_page(self) -> int:
        return self._current_page

    @property
    def total_pages(self) -> int:
        return self._total_pages

    @property
    def game_buttons(self) -> list[Button]:
        return list(self._game_buttons)

    @property
    def nav_buttons(self) -> list[Button]:
        return list(self._nav_buttons)
