"""プレイヤー登録画面。最大4人まで追加・削除、≥2人で開始可能。"""
from __future__ import annotations

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer


class PlayerRegisterScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._buttons: list[Button] = []
        self._title_r: TextRenderer | None = None
        self._name_r: TextRenderer | None = None

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 18), colors.INK_DARK)
        self._name_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 14), colors.INK_DARK)
        self._rebuild_buttons()

    def on_exit(self) -> None:
        pass

    def _rebuild_buttons(self) -> None:
        self._buttons = []
        if self._ctx.players.count < 4:
            self._buttons.append(Button(
                rect=pygame.Rect(20, 250, 140, 50),
                label="+ ADD",
                on_tap=self._open_keyboard,
                bg_color=colors.ACCENT_LIME,
            ))
        self._buttons.append(Button(
            rect=pygame.Rect(320, 250, 140, 50),
            label="START",
            on_tap=self._start,
            bg_color=colors.BG_SECONDARY,
            enabled=self._ctx.players.can_start(),
        ))
        for i, p in enumerate(self._ctx.players.players):
            self._buttons.append(Button(
                rect=pygame.Rect(360, 60 + i * 40, 100, 30),
                label="REMOVE",
                on_tap=lambda idx=i: self._remove(idx),
                bg_color=colors.DANGER_RED,
                fg_color=colors.INK_LIGHT,
            ))

    def _open_keyboard(self) -> None:
        from nomiboy.scenes.keyboard_input import KeyboardInputScene
        self._sm.push(KeyboardInputScene(self._sm, on_confirm=self._on_name_confirmed))

    def _on_name_confirmed(self, name: str) -> None:
        try:
            self._ctx.players.add(name)
        except ValueError:
            pass
        self._rebuild_buttons()

    def _remove(self, idx: int) -> None:
        self._ctx.players.remove(idx)
        self._rebuild_buttons()

    def _start(self) -> None:
        if not self._ctx.players.can_start():
            return
        from nomiboy.scenes.game_select import GameSelectScene
        self._sm.replace(GameSelectScene(self._sm))

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        self._title_r.draw(surface, f"PLAYERS  {self._ctx.players.count}/4", (config.SCREEN_SIZE[0] // 2, 30), anchor="center")
        for i, p in enumerate(self._ctx.players.players):
            pygame.draw.circle(surface, p.color, (40, 75 + i * 40), 12)
            self._name_r.draw(surface, p.name, (70, 75 + i * 40), anchor="midleft")
        for b in self._buttons:
            b.draw(surface, self._name_r)
