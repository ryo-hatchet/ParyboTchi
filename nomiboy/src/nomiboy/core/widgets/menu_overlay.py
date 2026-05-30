"""グローバル MENU オーバーレイ。

タイトルとキーボード以外のシーンの右上に MENU ボタンを表示し、
タップすると BACK TO TITLE / SELECT GAMES のモーダルを開く。
"""
from __future__ import annotations

from typing import Any

import pygame

from nomiboy import colors, config
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.button import Button


_MENU_BTN_RECT = pygame.Rect(398, 8, 74, 26)
_POPUP_BTN_W = 220
_POPUP_BTN_H = 52
_POPUP_BACK_RECT = pygame.Rect(
    (config.SCREEN_SIZE[0] - _POPUP_BTN_W) // 2, 110, _POPUP_BTN_W, _POPUP_BTN_H
)
_POPUP_SELECT_RECT = pygame.Rect(
    (config.SCREEN_SIZE[0] - _POPUP_BTN_W) // 2, 180, _POPUP_BTN_W, _POPUP_BTN_H
)


class MenuOverlay:
    def __init__(self, sm: Any, ctx: Any) -> None:
        self._sm = sm
        self._ctx = ctx
        self._open = False
        self._menu_btn = Button(
            rect=_MENU_BTN_RECT.copy(),
            label="MENU",
            on_tap=self._toggle,
            bg_color=colors.ACCENT_BERRY,
            fg_color=colors.INK_LIGHT,
        )
        self._back_btn = Button(
            rect=_POPUP_BACK_RECT.copy(),
            label="BACK TO TITLE",
            on_tap=self._back_to_title,
            bg_color=colors.BG_SECONDARY,
            fg_color=colors.INK_DARK,
        )
        self._select_btn = Button(
            rect=_POPUP_SELECT_RECT.copy(),
            label="SELECT GAMES",
            on_tap=self._select_games,
            bg_color=colors.ACCENT_LIME,
            fg_color=colors.INK_DARK,
        )

    # ─────────── 公開 API ───────────

    @property
    def is_open(self) -> bool:
        return self._open

    @property
    def menu_button_rect(self) -> pygame.Rect:
        return self._menu_btn.rect

    @property
    def back_to_title_rect(self) -> pygame.Rect:
        return self._back_btn.rect

    @property
    def select_games_rect(self) -> pygame.Rect:
        return self._select_btn.rect

    def is_visible_for(self, scene: Any) -> bool:
        if scene is None:
            return False
        return bool(getattr(scene, "show_menu", True))

    def handle_event(self, event: InputEvent) -> bool:
        """イベントを消費したら True。"""
        if event.kind != InputKind.TAP:
            return False
        if self._open:
            if self._back_btn.handle(event):
                return True
            if self._select_btn.handle(event):
                return True
            # ポップアップ外タップで閉じる
            self._open = False
            return True
        # 閉じている時は MENU ボタンのみ反応
        if self._menu_btn.handle(event):
            return True
        return False

    def draw(self, surface: pygame.Surface, text_renderer: Any) -> None:
        self._menu_btn.draw(surface, text_renderer)
        if self._open:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            surface.blit(overlay, (0, 0))
            self._back_btn.draw(surface, text_renderer)
            self._select_btn.draw(surface, text_renderer)

    # ─────────── 内部 ───────────

    def _toggle(self) -> None:
        self._open = not self._open

    def _back_to_title(self) -> None:
        from nomiboy.scenes.title import TitleScene

        self._ctx.players.clear()
        self._open = False
        self._sm.reset_to(TitleScene(self._sm))

    def _select_games(self) -> None:
        from nomiboy.scenes.game_select import GameSelectScene

        self._open = False
        self._sm.reset_to(GameSelectScene(self._sm))
