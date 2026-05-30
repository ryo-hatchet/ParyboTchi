"""AI 山手線ゲーム — お題に対してプレイヤーが回答、Gemini がジャッジ。"""
from __future__ import annotations

import json
import logging
import random
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum
from pathlib import Path

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer
from nomiboy.stores.player_store import Player

log = logging.getLogger(__name__)

_TOPICS_PATH = config.DATA_DIR / "yamanote_topics.json"
_MAX_NAME_LEN = 12


def _load_topics() -> list[str]:
    try:
        return json.loads(_TOPICS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["中華料理の名前", "アニメのタイトル", "47都道府県"]


class YamanoteState(Enum):
    PROMPT = "prompt"            # お題提示 + 「次の人タップして開始」
    INPUTTING = "inputting"      # キーボード入力中
    JUDGING = "judging"          # Gemini ジャッジ中
    OK_REVEAL = "ok_reveal"      # OK 結果表示 (1.5s)
    NG_REVEAL = "ng_reveal"      # NG 結果表示 → 飲む
    DONE = "done"                # 完走 (全員 5 周)


class YamanoteScene:
    show_menu = True

    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._state: YamanoteState = YamanoteState.PROMPT
        self._t: float = 0.0
        self._topic: str = ""
        self._history: list[str] = []
        self._current_player_idx: int = 0
        self._current_answer: str = ""
        self._loser: Player | None = None
        self._ai_comment: str = ""
        self._round_count: int = 0
        self._max_rounds: int = 0  # プレイヤー数 × 2 周
        self._future: Future | None = None
        self._executor: ThreadPoolExecutor | None = None
        # 描画
        self._title_r: TextRenderer | None = None
        self._sub_r: TextRenderer | None = None
        self._answer_r: TextRenderer | None = None
        self._buttons: list[Button] = []

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 22), colors.INK_LIGHT
        )
        self._sub_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 14), colors.INK_LIGHT
        )
        self._answer_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 18), colors.INK_LIGHT
        )
        topics = _load_topics()
        self._topic = random.choice(topics)
        self._history = []
        self._current_player_idx = 0
        self._round_count = 0
        self._max_rounds = max(2, len(ctx.players.players)) * 2
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._state = YamanoteState.PROMPT
        self._t = 0.0
        self._build_prompt_buttons()
        log.info("Yamanote start: topic=%s max_rounds=%d", self._topic, self._max_rounds)

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
        if self._state == YamanoteState.JUDGING:
            self._update_judging()
        elif self._state == YamanoteState.OK_REVEAL:
            if self._t >= 1.5:
                self._advance_player()
        elif self._state == YamanoteState.DONE:
            if self._t >= 3.0:
                self._sm.pop()

    def draw(self, surface: pygame.Surface) -> None:
        if self._ctx is not None:
            self._draw_bg(surface)
        if self._state == YamanoteState.PROMPT:
            self._draw_prompt(surface)
        elif self._state == YamanoteState.INPUTTING:
            self._draw_inputting(surface)
        elif self._state == YamanoteState.JUDGING:
            self._draw_judging(surface)
        elif self._state == YamanoteState.OK_REVEAL:
            self._draw_ok_reveal(surface)
        elif self._state == YamanoteState.NG_REVEAL:
            self._draw_ng_reveal(surface)
        elif self._state == YamanoteState.DONE:
            self._draw_done(surface)
        for b in self._buttons:
            b.draw(surface, self._sub_r)

    # ─────────── ボタン構築 ───────────

    def _build_prompt_buttons(self) -> None:
        self._buttons = [
            Button(
                rect=pygame.Rect(160, 240, 160, 50),
                label="入力 START",
                on_tap=self._open_keyboard,
                bg_color=colors.BG_SECONDARY,
            ),
        ]

    def _build_ng_buttons(self) -> None:
        self._buttons = [
            Button(
                rect=pygame.Rect(280, 270, 180, 36),
                label="GameSelect へ →",
                on_tap=self._sm.pop,
                bg_color=colors.BG_SECONDARY,
            ),
        ]

    # ─────────── 状態遷移 ───────────

    def _open_keyboard(self) -> None:
        from nomiboy.scenes.keyboard_input import KeyboardInputScene
        self._buttons = []
        self._state = YamanoteState.INPUTTING
        self._sm.push(
            KeyboardInputScene(self._sm, on_confirm=self._on_input_confirmed)
        )

    def _on_input_confirmed(self, text: str) -> None:
        # KeyboardInputScene が pop された後にこのコールバックが走る
        self._current_answer = text.strip()
        if not self._current_answer:
            self._state = YamanoteState.PROMPT
            self._build_prompt_buttons()
            return
        self._state = YamanoteState.JUDGING
        self._t = 0.0
        self._buttons = []
        if self._ctx is None:
            self._state = YamanoteState.PROMPT
            self._build_prompt_buttons()
            return
        # KeyboardInputScene push 時に on_exit で executor が止められているので再構築
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1)
        self._future = self._executor.submit(
            self._ctx.lyrics.judge_yamanote_answer,
            self._topic,
            self._current_answer,
            list(self._history),
        )

    def _update_judging(self) -> None:
        if self._future is None:
            return
        if not self._future.done():
            if self._t >= 10.0:
                # タイムアウト → OK 扱いで進める
                self._on_judged(True, "判定 TIMEOUT")
            return
        try:
            result = self._future.result()
        except Exception as e:
            log.warning("Yamanote judge future error: %s", e)
            result = None
        if result is None:
            # 失敗 → OK 扱い
            self._on_judged(True, "")
        else:
            ok, comment = result
            self._on_judged(ok, comment)

    def _on_judged(self, ok: bool, comment: str) -> None:
        self._ai_comment = comment
        if ok:
            self._history.append(self._current_answer)
            self._state = YamanoteState.OK_REVEAL
            self._t = 0.0
            self._buttons = []
            # TTS で読み上げ
            if self._ctx is not None and self._ctx.online:
                try:
                    self._ctx.tts.speak(self._current_answer)
                except Exception:
                    pass
        else:
            self._state = YamanoteState.NG_REVEAL
            self._t = 0.0
            players = self._ctx.players.players if self._ctx else []
            if players:
                self._loser = players[self._current_player_idx % len(players)]
            if self._ctx is not None and self._ctx.online and comment:
                try:
                    self._ctx.tts.speak(comment)
                except Exception:
                    pass
            self._build_ng_buttons()

    def _advance_player(self) -> None:
        if self._ctx is None:
            return
        players = self._ctx.players.players
        if not players:
            self._state = YamanoteState.DONE
            self._t = 0.0
            return
        self._current_player_idx = (self._current_player_idx + 1) % len(players)
        self._round_count += 1
        if self._round_count >= self._max_rounds:
            self._state = YamanoteState.DONE
            self._t = 0.0
            return
        self._state = YamanoteState.PROMPT
        self._t = 0.0
        self._build_prompt_buttons()

    # ─────────── 描画 ───────────

    def _draw_bg(self, surface: pygame.Surface) -> None:
        try:
            raw = self._ctx.assets.image("images/background.png")  # type: ignore[union-attr]
            scaled = pygame.transform.smoothscale(raw, config.SCREEN_SIZE)
            if colors.INVERT_COLORS:
                inv = pygame.Surface(scaled.get_size())
                inv.fill((255, 255, 255))
                inv.blit(scaled, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
                scaled = inv
            surface.blit(scaled, (0, 0))
            overlay = pygame.Surface(config.SCREEN_SIZE, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            surface.blit(overlay, (0, 0))
        except Exception:
            surface.fill(colors.INK_DARK)

    def _draw_prompt(self, surface: pygame.Surface) -> None:
        if self._ctx is None:
            return
        cx = config.SCREEN_SIZE[0] // 2
        self._sub_r.draw(
            surface,
            f"Round {self._round_count + 1} / {self._max_rounds}",
            (cx, 20),
            anchor="center",
        )
        self._title_r.draw(
            surface, f"お題: {self._topic}", (cx, 70), anchor="center"
        )
        players = self._ctx.players.players
        if players:
            player = players[self._current_player_idx % len(players)]
            self._title_r.draw(
                surface,
                f"{player.name} の番",
                (cx, 140),
                anchor="center",
                color=player.color,
            )
            pygame.draw.circle(surface, player.color, (cx, 190), 18)
        if self._history:
            hist_text = " / ".join(self._history[-3:])
            self._sub_r.draw(surface, f"既出: {hist_text}", (cx, 215), anchor="center")

    def _draw_inputting(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        self._sub_r.draw(surface, "キーボードで入力中…", (cx, 150), anchor="center")

    def _draw_judging(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        self._title_r.draw(surface, "AI 判定中…", (cx, 100), anchor="center")
        self._answer_r.draw(
            surface, f"「{self._current_answer}」", (cx, 160), anchor="center"
        )
        dots = "." * (1 + int(self._t * 3) % 4)
        self._sub_r.draw(surface, dots, (cx, 220), anchor="center")

    def _draw_ok_reveal(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        self._title_r.draw(
            surface, "◯ OK!", (cx, 100), anchor="center", color=colors.ACCENT_LIME
        )
        self._answer_r.draw(
            surface, f"「{self._current_answer}」", (cx, 160), anchor="center"
        )

    def _draw_ng_reveal(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        self._title_r.draw(
            surface, "× NG!", (cx, 50), anchor="center", color=colors.DANGER_RED
        )
        self._answer_r.draw(
            surface, f"「{self._current_answer}」", (cx, 100), anchor="center"
        )
        if self._ai_comment:
            self._sub_r.draw(
                surface,
                f"AI: {self._ai_comment}",
                (cx, 140),
                anchor="center",
                color=colors.WARNING_AMBER,
            )
        if self._loser:
            self._title_r.draw(
                surface,
                f"{self._loser.name} は飲む！",
                (cx, 190),
                anchor="center",
                color=self._loser.color,
            )

    def _draw_done(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        cy = config.SCREEN_SIZE[1] // 2
        self._title_r.draw(surface, "🍺 完走！ 🍺", (cx, cy - 30), anchor="center")
        self._sub_r.draw(surface, "全員乾杯！", (cx, cy + 10), anchor="center")
