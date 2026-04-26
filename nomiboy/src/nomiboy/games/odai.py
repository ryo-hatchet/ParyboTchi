"""お題ゲーム（○○な人は飲む）。"""
from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass
from pathlib import Path

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer

log = logging.getLogger(__name__)


FALLBACK_CARDS = [
    {"id": "f1", "text": "今日一番元気な人"},
    {"id": "f2", "text": "最近一番遅く寝た人"},
    {"id": "f3", "text": "今月誕生日が一番近い人"},
    {"id": "f4", "text": "メガネをかけている人"},
    {"id": "f5", "text": "今日コーヒーを飲んだ人"},
]


@dataclass(frozen=True)
class OdaiCard:
    id: str
    text: str


class OdaiController:
    def __init__(
        self,
        cards: list[OdaiCard],
        rng: random.Random | None = None,
        recent_window: int = 3,
    ) -> None:
        self._cards = cards
        self._rng = rng or random.Random()
        self._recent: list[str] = []
        self._window = recent_window

    @staticmethod
    def load_cards(path: Path) -> list[OdaiCard]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [OdaiCard(id=d["id"], text=d["text"]) for d in data]
        except (OSError, ValueError, KeyError) as e:
            log.warning("odai_cards.json load failed (%s), using fallback", e)
            return [OdaiCard(id=d["id"], text=d["text"]) for d in FALLBACK_CARDS]

    def next_card(self) -> OdaiCard:
        candidates = [c for c in self._cards if c.id not in self._recent] or self._cards
        card = self._rng.choice(candidates)
        self._recent.append(card.id)
        if len(self._recent) > self._window:
            self._recent.pop(0)
        return card


class OdaiScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._ctrl: OdaiController | None = None
        self._current: OdaiCard | None = None
        self._title_r: TextRenderer | None = None
        self._body_r: TextRenderer | None = None
        self._buttons: list[Button] = []

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        cards = OdaiController.load_cards(config.DATA_DIR / "odai_cards.json")
        self._ctrl = OdaiController(cards=cards)
        self._title_r = TextRenderer(ctx.assets.font("DotGothic16-Regular.ttf", 14), colors.INK_DARK)
        self._body_r = TextRenderer(ctx.assets.font("DotGothic16-Regular.ttf", 18), colors.INK_DARK)
        self._buttons = [
            Button(pygame.Rect(10, 10, 80, 26), "BACK", self._sm.pop, bg_color=colors.ACCENT_BERRY, fg_color=colors.INK_LIGHT),
            Button(pygame.Rect(40, 250, 160, 50), "NEXT", self._next, bg_color=colors.BG_SECONDARY),
            Button(pygame.Rect(280, 250, 160, 50), "QUIT", self._sm.pop, bg_color=colors.ACCENT_BERRY, fg_color=colors.INK_LIGHT),
        ]
        self._next()

    def on_exit(self) -> None:
        pass

    def _next(self) -> None:
        self._current = self._ctrl.next_card()
        if self._ctx.online:
            self._ctx.tts.speak(self._current.text + " は飲む！")

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        self._title_r.draw(surface, "ODAI", (config.SCREEN_SIZE[0] // 2, 50), anchor="center")
        if self._current:
            self._wrap_draw(surface, self._current.text + " は飲む！", y=130)
        for b in self._buttons:
            b.draw(surface, self._title_r)

    def _wrap_draw(self, surface: pygame.Surface, text: str, y: int) -> None:
        line_len = 13
        lines = [text[i:i + line_len] for i in range(0, len(text), line_len)]
        for i, line in enumerate(lines):
            self._body_r.draw(surface, line, (config.SCREEN_SIZE[0] // 2, y + i * 30), anchor="center")
