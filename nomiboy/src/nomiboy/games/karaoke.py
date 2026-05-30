"""飲みゲーカラオケ。Gemini Flash で歌詞生成 → Lyria 3 Pro で楽曲化 → 全員で聴く。"""
from __future__ import annotations

import json
import logging
import random
import re
import tempfile
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum
from pathlib import Path

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.lyrics_service import LyricsService, _default_lyrics
from nomiboy.core.lyria_service import LyriaService
from nomiboy.core.widgets.text import TextRenderer
from nomiboy.scenes.game_start_intro import _draw_beer_mug

log = logging.getLogger(__name__)


class KaraokeState(Enum):
    GENERATING = "generating"
    PLAYING = "playing"
    KANPAI = "kanpai"
    ERROR = "error"


def _load_genres(path: Path) -> list[str]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["J-POP", "ロック", "EDM"]


def _build_lyria_prompt(genre: str, lyrics: str, duration_sec: int) -> str:
    """歌詞 + スタイル + 長さを 1 つの Lyria プロンプトに統合。"""
    return (
        f"Genre: {genre}. Japanese karaoke party song with crowd cheering. "
        f"Duration: about {duration_sec} seconds. Energetic vocals.\n\n"
        f"{lyrics}"
    )


def _parse_lyric_lines(raw: str) -> list[str]:
    """Lyrics: テキストから歌詞行のみ抽出（[Verse] 等のタグ除外、空行除外）。"""
    lines: list[str] = []
    if "Lyrics:" in raw:
        body = raw.split("Lyrics:", 1)[1]
    else:
        body = raw
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        if re.fullmatch(r"\[[^\]]+\]", s):
            continue
        lines.append(s)
    return lines or ["乾杯！"]


class KaraokeScene:
    show_menu = True

    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._state: KaraokeState = KaraokeState.GENERATING
        self._t: float = 0.0
        self._genre: str = ""
        self._lyric_lines: list[str] = []
        self._error_message: str = ""
        self._tmp_path: Path | None = None
        self._future: Future | None = None
        self._executor: ThreadPoolExecutor | None = None
        # 描画リソース
        self._title_r: TextRenderer | None = None
        self._sub_r: TextRenderer | None = None
        self._lyric_r: TextRenderer | None = None

    # ─────────── ライフサイクル ───────────

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 22), colors.INK_LIGHT
        )
        self._sub_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 14), colors.INK_LIGHT
        )
        self._lyric_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 16), colors.INK_LIGHT
        )

        genres = _load_genres(config.KARAOKE_GENRES_PATH)
        self._genre = random.choice(genres)
        players = ctx.players.players
        if not players:
            self._state = KaraokeState.ERROR
            self._error_message = "プレイヤーがいません"
            return
        if not ctx.online:
            self._state = KaraokeState.ERROR
            self._error_message = "ネット接続が必要です"
            return

        # コール度をランダムに割り振り (0.1〜1.0)
        emphasis = {p.name: round(random.uniform(0.1, 1.0), 2) for p in players}
        log.info("Karaoke start: genre=%s emphasis=%s", self._genre, emphasis)

        self._executor = ThreadPoolExecutor(max_workers=1)
        self._future = self._executor.submit(
            self._generate_song,
            ctx.lyrics,
            ctx.call_player._lyria,  # type: ignore[attr-defined]
            self._genre,
            emphasis,
        )
        self._state = KaraokeState.GENERATING
        self._t = 0.0

    def on_exit(self) -> None:
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
        if self._future is not None:
            self._future.cancel()
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None
        if self._tmp_path is not None:
            try:
                self._tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

    def handle_event(self, event: InputEvent) -> None:
        # 期間中タップは無効（MENU だけ反応する仕様、Menu は App 層で吸われる）
        pass

    def update(self, dt: float) -> None:
        self._t += dt
        if self._state == KaraokeState.GENERATING:
            self._update_generating()
        elif self._state == KaraokeState.PLAYING:
            self._update_playing()
        elif self._state == KaraokeState.KANPAI:
            if self._t >= config.KARAOKE_KANPAI_SEC:
                self._sm.pop()
        elif self._state == KaraokeState.ERROR:
            if self._t >= 5.0:
                self._sm.pop()

    def draw(self, surface: pygame.Surface) -> None:
        if self._ctx is not None:
            self._draw_bg(surface)
        if self._state == KaraokeState.GENERATING:
            self._draw_generating(surface)
        elif self._state == KaraokeState.PLAYING:
            self._draw_playing(surface)
        elif self._state == KaraokeState.KANPAI:
            self._draw_kanpai(surface)
        elif self._state == KaraokeState.ERROR:
            self._draw_error(surface)

    # ─────────── 内部 ───────────

    def _generate_song(
        self,
        lyrics_svc: LyricsService,
        lyria_svc: LyriaService,
        genre: str,
        emphasis: dict[str, float],
    ) -> tuple[str, bytes] | None:
        """歌詞生成 → 楽曲生成。(lyrics_text, audio_bytes) を返す。失敗時 None。"""
        lyrics = lyrics_svc.generate_song_lyrics(genre, emphasis)
        if not lyrics:
            log.warning("Lyrics generation failed, using default")
            lyrics = _default_lyrics(genre, list(emphasis.keys()))
        prompt = _build_lyria_prompt(genre, lyrics, config.KARAOKE_DURATION_SEC)
        audio = lyria_svc.synthesize_song(prompt)
        if not audio:
            log.warning("Lyria song generation returned None")
            return None
        return (lyrics, audio)

    def _update_generating(self) -> None:
        if self._future is None:
            return
        if self._future.done():
            try:
                result = self._future.result()
            except Exception as e:
                log.warning("Karaoke generation future error: %s", e)
                result = None
            if result is None:
                self._state = KaraokeState.ERROR
                self._error_message = "生成に失敗しました"
                self._t = 0.0
                return
            lyrics_text, audio_bytes = result
            self._lyric_lines = _parse_lyric_lines(lyrics_text)
            # 一時ファイルに書き出して mixer.music で再生
            try:
                self._tmp_path = Path(
                    tempfile.mkstemp(suffix=".mp3", prefix="nomiboy-karaoke-")[1]
                )
                self._tmp_path.write_bytes(audio_bytes)
                pygame.mixer.music.load(str(self._tmp_path))
                pygame.mixer.music.set_volume(1.0)
                pygame.mixer.music.play()
                self._state = KaraokeState.PLAYING
                self._t = 0.0
                log.info(
                    "Karaoke playing: %d lyric lines, %d audio bytes",
                    len(self._lyric_lines),
                    len(audio_bytes),
                )
            except Exception as e:
                log.warning("Karaoke playback start failed: %s", e)
                self._state = KaraokeState.ERROR
                self._error_message = "再生に失敗しました"
                self._t = 0.0
        elif self._t >= config.KARAOKE_GENERATE_TIMEOUT_SEC:
            self._state = KaraokeState.ERROR
            self._error_message = "タイムアウトしました"
            self._t = 0.0

    def _update_playing(self) -> None:
        # 曲が止まる or 長すぎたら KANPAI へ
        if not pygame.mixer.music.get_busy():
            self._state = KaraokeState.KANPAI
            self._t = 0.0
            return
        if self._t >= config.KARAOKE_DURATION_SEC + 20:
            pygame.mixer.music.stop()
            self._state = KaraokeState.KANPAI
            self._t = 0.0

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
            overlay.fill((0, 0, 0, 160))
            surface.blit(overlay, (0, 0))
        except Exception:
            surface.fill(colors.INK_DARK)

    def _draw_generating(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        self._title_r.draw(surface, "🎤 カラオケ生成中…", (cx, 70), anchor="center")
        self._sub_r.draw(surface, f"ジャンル: {self._genre}", (cx, 120), anchor="center")
        # プログレスバー
        bar_w = 360
        bar_h = 20
        bx = (config.SCREEN_SIZE[0] - bar_w) // 2
        by = 170
        pygame.draw.rect(surface, colors.INK_LIGHT, (bx, by, bar_w, bar_h), width=2)
        progress = min(self._t / 30.0, 1.0)
        pygame.draw.rect(
            surface, colors.BG_SECONDARY, (bx + 2, by + 2, int((bar_w - 4) * progress), bar_h - 4)
        )
        self._sub_r.draw(
            surface, f"{int(self._t)}s / 30s", (cx, by + bar_h + 16), anchor="center"
        )
        _draw_beer_mug(surface, cx, 270, size=50)

    def _draw_playing(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        self._sub_r.draw(surface, f"♪ {self._genre}", (20, 20), anchor="topleft")
        # 歌詞行送り: 全行数を時間で均等割
        if self._lyric_lines:
            duration = max(1.0, float(config.KARAOKE_DURATION_SEC))
            idx = int((self._t / duration) * len(self._lyric_lines))
            visible = self._lyric_lines[max(0, idx - 1) : idx + 2]
            for i, line in enumerate(visible):
                y = 120 + i * 38
                color = colors.BG_SECONDARY if i == 1 else colors.INK_LIGHT
                self._lyric_r.draw(surface, line, (cx, y), anchor="center", color=color)
        # 進行バー
        bar_w = 360
        bar_h = 8
        bx = (config.SCREEN_SIZE[0] - bar_w) // 2
        by = 290
        pygame.draw.rect(surface, colors.INK_LIGHT, (bx, by, bar_w, bar_h), width=1)
        progress = min(self._t / max(1.0, float(config.KARAOKE_DURATION_SEC)), 1.0)
        pygame.draw.rect(
            surface, colors.BG_SECONDARY, (bx + 1, by + 1, int((bar_w - 2) * progress), bar_h - 2)
        )

    def _draw_kanpai(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        cy = config.SCREEN_SIZE[1] // 2
        self._title_r.draw(surface, "🍺 乾杯！ 🍺", (cx, cy - 60), anchor="center")
        self._sub_r.draw(surface, "かんぱい！ かんぱい！", (cx, cy - 20), anchor="center")
        _draw_beer_mug(surface, cx, cy + 50, size=80)

    def _draw_error(self, surface: pygame.Surface) -> None:
        cx = config.SCREEN_SIZE[0] // 2
        cy = config.SCREEN_SIZE[1] // 2
        self._title_r.draw(surface, "エラー", (cx, cy - 40), anchor="center")
        self._sub_r.draw(surface, self._error_message, (cx, cy + 10), anchor="center")
        self._sub_r.draw(surface, "(5 秒で戻ります)", (cx, cy + 50), anchor="center")
