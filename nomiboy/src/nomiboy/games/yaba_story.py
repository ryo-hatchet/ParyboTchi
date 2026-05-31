"""AI ヤバ物語 — Gemini が全員主役の短編ヤバストーリーを生成、ヤバい主役が飲む。"""
from __future__ import annotations

import logging
import random
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer
from nomiboy.scenes.game_start_intro import _draw_beer_mug

log = logging.getLogger(__name__)


class YabaStoryState(Enum):
    LOADING = "loading"
    STORY = "story"
    REVEAL = "reveal"
    ERROR = "error"


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """日本語混じり文字列を max_chars 文字で折り返す簡易ラッパー。"""
    lines: list[str] = []
    line = ""
    for ch in text:
        if ch == "\n":
            lines.append(line)
            line = ""
            continue
        line += ch
        if len(line) >= max_chars:
            lines.append(line)
            line = ""
    if line:
        lines.append(line)
    return lines


class YabaStoryScene:
    show_menu = True

    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._state: YabaStoryState = YabaStoryState.LOADING
        self._t: float = 0.0
        self._story: str = ""
        self._loser_name: str = ""
        self._reason: str = ""
        self._story_lines: list[str] = []
        self._error_message: str = ""
        self._future: Future | None = None
        self._executor: ThreadPoolExecutor | None = None
        self._title_r: TextRenderer | None = None
        self._sub_r: TextRenderer | None = None
        self._body_r: TextRenderer | None = None
        self._buttons: list[Button] = []

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 22), colors.INK_LIGHT
        )
        self._sub_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 14), colors.INK_LIGHT
        )
        self._body_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 14), colors.INK_LIGHT
        )
        players = ctx.players.players
        if not players:
            self._state = YabaStoryState.ERROR
            self._error_message = "プレイヤーがいません"
            return
        names = [p.name for p in players]
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._future = self._executor.submit(ctx.lyrics.generate_yaba_story, names)
        self._state = YabaStoryState.LOADING
        self._t = 0.0

    def on_exit(self) -> None:
        if self._future is not None:
            self._future.cancel()
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None

    def handle_event(self, event: InputEvent) -> None:
        if event.kind != InputKind.TAP:
            return
        for b in self._buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        self._t += dt
        if self._state == YabaStoryState.LOADING:
            self._update_loading()
        elif self._state == YabaStoryState.ERROR:
            if self._t >= 5.0:
                self._sm.pop()

    def draw(self, surface: pygame.Surface) -> None:
        if self._ctx is not None:
            self._draw_bg(surface)
        if self._state == YabaStoryState.LOADING:
            self._draw_loading(surface)
        elif self._state == YabaStoryState.STORY:
            self._draw_story(surface)
        elif self._state == YabaStoryState.REVEAL:
            self._draw_reveal(surface)
        elif self._state == YabaStoryState.ERROR:
            self._draw_error(surface)
        for b in self._buttons:
            b.draw(surface, self._sub_r)

    # ─────────── 内部 ───────────

    def _update_loading(self) -> None:
        if self._future is None:
            return
        if self._future.done():
            try:
                result = self._future.result()
            except Exception as e:
                log.warning("Yaba story future error: %s", e)
                result = None
            if result is None:
                self._fallback_story()
            else:
                self._story, self._loser_name, self._reason = result
            self._story_lines = _wrap_text(self._story, 22)
            self._state = YabaStoryState.STORY
            self._t = 0.0
            log.info(
                "YabaStory loaded: loser=%s reason=%s story_len=%d",
                self._loser_name,
                self._reason,
                len(self._story),
            )
            self._buttons = [
                Button(
                    rect=pygame.Rect(280, 270, 180, 36),
                    label="飲む人発表 →",
                    on_tap=self._reveal,
                    bg_color=colors.BG_SECONDARY,
                ),
            ]

    def _fallback_story(self) -> None:
        if self._ctx is None:
            return
        players = self._ctx.players.players
        names = [p.name for p in players]
        self._story = (
            f"今夜の居酒屋、{'、'.join(names)} が集合！\n"
            "誰もが一気に乾杯した瞬間、最も派手にコケた者が伝説となった…"
        )
        self._loser_name = random.choice(names)
        self._reason = "派手にコケた罪"

    def _reveal(self) -> None:
        self._state = YabaStoryState.REVEAL
        self._t = 0.0
        self._buttons = [
            Button(
                rect=pygame.Rect(280, 270, 180, 36),
                label="GameSelect へ →",
                on_tap=self._sm.pop,
                bg_color=colors.BG_SECONDARY,
            ),
        ]

    def _find_loser(self):
        """名前で player を検索（部分一致も許容）。"""
        if self._ctx is None:
            return None
        for p in self._ctx.players.players:
            if p.name == self._loser_name:
                return p
        # 部分一致 fallback
        for p in self._ctx.players.players:
            if self._loser_name in p.name or p.name in self._loser_name:
                return p
        # 最後の砦: ランダム
        if self._ctx.players.players:
            return random.choice(self._ctx.players.players)
        return None

    # ─────────── 描画 ───────────

    def _draw_bg(self, surface: pygame.Surface) -> None:
        try:
            from nomiboy.core.widgets.bg import load_background
            bg = load_background(self._ctx, "images/background.png", config.SCREEN_SIZE)
            surface.blit(bg, (0, 0))
            overlay = pygame.Surface(config.SCREEN_SIZE, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
        except Exception:
            surface.fill(colors.INK_DARK)

    def _draw_loading(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        self._title_r.draw(surface, "🍶 ヤバ物語 を執筆中…", (cx, 100), anchor="center")
        dots = "." * (1 + int(self._t * 3) % 4)
        self._sub_r.draw(surface, dots, (cx, 160), anchor="center")
        _draw_beer_mug(surface, cx, 230, size=60)

    def _draw_story(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        self._title_r.draw(surface, "🍶 ヤバ物語", (cx, 20), anchor="center")
        # 本文を行送り
        y = 60
        for line in self._story_lines[:9]:
            self._body_r.draw(surface, line, (cx, y), anchor="center")
            y += 22

    def _draw_reveal(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        loser = self._find_loser()
        self._title_r.draw(
            surface, "🍺 ヤバいやつは…", (cx, 50), anchor="center", color=colors.DANGER_RED
        )
        if loser is not None:
            pygame.draw.circle(surface, loser.color, (cx, 130), 36)
            self._title_r.draw(
                surface,
                loser.name,
                (cx, 180),
                anchor="center",
                color=colors.INK_LIGHT,
            )
            self._sub_r.draw(
                surface,
                f"理由: {self._reason}",
                (cx, 215),
                anchor="center",
                color=colors.INK_LIGHT,
            )
            self._title_r.draw(
                surface,
                "飲んで！",
                (cx, 250),
                anchor="center",
                color=colors.DANGER_RED,
            )

    def _draw_error(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        self._title_r.draw(surface, "エラー", (cx, 120), anchor="center")
        self._sub_r.draw(surface, self._error_message, (cx, 170), anchor="center")
