"""少数派 SHOT — Gemini 生成の YES/NO 質問に全員投票、少数派が飲む。"""
from __future__ import annotations

import logging
import random
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer
from nomiboy.stores.player_store import Player

log = logging.getLogger(__name__)


_ROUNDS = 5


class MinorityState(Enum):
    LOADING = "loading"
    VOTING = "voting"
    REVEAL = "reveal"
    DONE = "done"


@dataclass
class _RoundResult:
    question: str
    votes: dict[int, bool] = field(default_factory=dict)  # player_id -> True(YES)/False(NO)


class MinorityScene:
    show_menu = True

    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._state: MinorityState = MinorityState.LOADING
        self._t: float = 0.0
        self._questions: list[str] = []
        self._round_idx: int = 0
        self._current_player_idx: int = 0
        self._results: list[_RoundResult] = []
        self._losers_this_round: list[Player] = []
        self._unanimous: bool = False
        # 非同期で質問生成
        self._future: Future | None = None
        self._executor: ThreadPoolExecutor | None = None
        # 描画
        self._title_r: TextRenderer | None = None
        self._sub_r: TextRenderer | None = None
        self._q_r: TextRenderer | None = None
        self._buttons: list[Button] = []

    # ─────────── ライフサイクル ───────────

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 22), colors.INK_LIGHT
        )
        self._sub_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 14), colors.INK_LIGHT
        )
        self._q_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 18), colors.INK_LIGHT
        )
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._future = self._executor.submit(
            ctx.lyrics.generate_minority_questions, _ROUNDS
        )
        self._state = MinorityState.LOADING
        self._t = 0.0

    def on_exit(self) -> None:
        if self._future is not None:
            self._future.cancel()
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    def handle_event(self, event: InputEvent) -> None:
        if event.kind != InputKind.TAP:
            return
        for b in self._buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        self._t += dt
        if self._state == MinorityState.LOADING:
            self._update_loading()
        elif self._state == MinorityState.REVEAL:
            if self._t >= 4.0:
                self._next_round()
        elif self._state == MinorityState.DONE:
            if self._t >= 3.0:
                self._sm.pop()

    def draw(self, surface: pygame.Surface) -> None:
        if self._ctx is not None:
            self._draw_bg(surface)
        if self._state == MinorityState.LOADING:
            self._draw_loading(surface)
        elif self._state == MinorityState.VOTING:
            self._draw_voting(surface)
        elif self._state == MinorityState.REVEAL:
            self._draw_reveal(surface)
        elif self._state == MinorityState.DONE:
            self._draw_done(surface)
        for b in self._buttons:
            b.draw(surface, self._sub_r)

    # ─────────── 内部 ───────────

    def _update_loading(self) -> None:
        if self._future is None:
            return
        if self._future.done():
            try:
                self._questions = self._future.result() or []
            except Exception as e:
                log.warning("Minority questions future error: %s", e)
                self._questions = []
            if not self._questions:
                from nomiboy.core.lyrics_service import _DEFAULT_MINORITY_QUESTIONS
                self._questions = list(_DEFAULT_MINORITY_QUESTIONS)
            log.info("Minority: %d questions loaded", len(self._questions))
            self._start_round()

    def _start_round(self) -> None:
        if self._round_idx >= min(_ROUNDS, len(self._questions)):
            self._state = MinorityState.DONE
            self._t = 0.0
            self._buttons = []
            return
        q = self._questions[self._round_idx]
        self._results.append(_RoundResult(question=q))
        self._current_player_idx = 0
        self._state = MinorityState.VOTING
        self._t = 0.0
        self._build_vote_buttons()

    def _build_vote_buttons(self) -> None:
        self._buttons = [
            Button(
                rect=pygame.Rect(40, 240, 160, 60),
                label="YES",
                on_tap=lambda: self._cast_vote(True),
                bg_color=colors.ACCENT_LIME,
                fg_color=colors.INK_DARK,
            ),
            Button(
                rect=pygame.Rect(280, 240, 160, 60),
                label="NO",
                on_tap=lambda: self._cast_vote(False),
                bg_color=colors.DANGER_RED,
                fg_color=colors.INK_LIGHT,
            ),
        ]

    def _cast_vote(self, yes: bool) -> None:
        if self._ctx is None:
            return
        players = self._ctx.players.players
        if self._current_player_idx >= len(players):
            return
        player = players[self._current_player_idx]
        self._results[-1].votes[player.id] = yes
        log.info("Minority vote: %s -> %s", player.name, "YES" if yes else "NO")
        self._current_player_idx += 1
        if self._current_player_idx >= len(players):
            self._compute_losers_and_reveal()
        else:
            self._build_vote_buttons()

    def _compute_losers_and_reveal(self) -> None:
        if self._ctx is None:
            return
        players = self._ctx.players.players
        votes = self._results[-1].votes
        yes_ids = [pid for pid, v in votes.items() if v]
        no_ids = [pid for pid, v in votes.items() if not v]
        if not yes_ids or not no_ids:
            # 全員一致 → 飲む人なし（全員乾杯）
            self._losers_this_round = []
            self._unanimous = True
        else:
            losers_ids = yes_ids if len(yes_ids) < len(no_ids) else no_ids
            self._losers_this_round = [p for p in players if p.id in losers_ids]
            self._unanimous = False
        self._state = MinorityState.REVEAL
        self._t = 0.0
        self._build_reveal_buttons()

    def _build_reveal_buttons(self) -> None:
        self._buttons = [
            Button(
                rect=pygame.Rect(280, 270, 180, 40),
                label="次の質問へ →",
                on_tap=self._next_round,
                bg_color=colors.BG_SECONDARY,
            ),
        ]

    def _next_round(self) -> None:
        self._round_idx += 1
        self._losers_this_round = []
        self._unanimous = False
        self._start_round()

    # ─────────── 描画 ───────────

    def _draw_bg(self, surface: pygame.Surface) -> None:
        try:
            from nomiboy.core.widgets.bg import load_background
            bg = load_background(self._ctx, "images/background.png", config.SCREEN_SIZE)
            surface.blit(bg, (0, 0))
            overlay = pygame.Surface(config.SCREEN_SIZE, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            surface.blit(overlay, (0, 0))
        except Exception:
            surface.fill(colors.INK_DARK)

    def _draw_loading(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        self._title_r.draw(surface, "少数派 SHOT", (cx, 100), anchor="center")
        self._sub_r.draw(surface, "質問を考え中…", (cx, 160), anchor="center")
        # 簡易スピナー（点が回る）
        dots = "." * (1 + int(self._t * 3) % 4)
        self._sub_r.draw(surface, dots, (cx, 200), anchor="center")

    def _draw_voting(self, surface: pygame.Surface) -> None:
        if self._ctx is None:
            return
        cx = config.SCREEN_SIZE[0] // 2
        # 上部: ラウンド表示
        self._sub_r.draw(
            surface,
            f"Q{self._round_idx + 1} / {min(_ROUNDS, len(self._questions))}",
            (cx, 20),
            anchor="center",
        )
        # 質問
        question = self._results[-1].question if self._results else ""
        self._q_r.draw(surface, question, (cx, 70), anchor="center")
        # 現在のプレイヤー強調
        players = self._ctx.players.players
        if self._current_player_idx < len(players):
            player = players[self._current_player_idx]
            self._title_r.draw(
                surface,
                f"{player.name} の番",
                (cx, 140),
                anchor="center",
                color=player.color,
            )
            pygame.draw.circle(surface, player.color, (cx, 200), 18)

    def _draw_reveal(self, surface: pygame.Surface) -> None:
        if self._ctx is None:
            return
        cx = config.SCREEN_SIZE[0] // 2
        votes = self._results[-1].votes
        yes_n = sum(1 for v in votes.values() if v)
        no_n = sum(1 for v in votes.values() if not v)
        self._sub_r.draw(
            surface,
            f"YES: {yes_n}  /  NO: {no_n}",
            (cx, 30),
            anchor="center",
        )
        if self._unanimous:
            self._title_r.draw(surface, "全員一致！", (cx, 90), anchor="center", color=colors.ACCENT_LIME)
            self._sub_r.draw(surface, "🍺 みんなで乾杯！ 🍺", (cx, 140), anchor="center")
        else:
            self._title_r.draw(surface, "少数派発見！", (cx, 90), anchor="center", color=colors.DANGER_RED)
            for i, p in enumerate(self._losers_this_round):
                y = 130 + i * 28
                self._sub_r.draw(
                    surface, f"{p.name} は 飲む！", (cx, y), anchor="center", color=p.color
                )

    def _draw_done(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        cy = config.SCREEN_SIZE[1] // 2
        self._title_r.draw(surface, "🍺 おつかれ乾杯！ 🍺", (cx, cy - 30), anchor="center")
        self._sub_r.draw(surface, "GameSelect に戻ります…", (cx, cy + 30), anchor="center")
