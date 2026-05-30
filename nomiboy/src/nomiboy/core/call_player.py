"""ドリンクコール再生サービス。ゲーム開始時に全員分をプリフェッチし、負け確定時に再生する。"""
from __future__ import annotations

import io
import json
import logging
import random
import tempfile
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Union

import pygame

from nomiboy.core.audio_service import AudioService
from nomiboy.core.lyria_service import CallTemplate, LyriaService
from nomiboy.stores.player_store import Player

log = logging.getLogger(__name__)

_DEFAULT_TEMPLATE = CallTemplate(
    style="upbeat J-pop party chant with crowd cheering",
    lyrics_template="Lyrics:\n[Chorus]\n{name} が飲んで！ 飲んで！ 飲んで！",
    duration_sec=10,
)

# _generate_one の戻り値: pygame.mixer.Sound または ("file", Path) で mixer.music 経由再生
Playable = Union[pygame.mixer.Sound, tuple[str, Path]]


def load_call_templates(path: Path) -> list[CallTemplate]:
    """JSON からテンプレ集をロード。失敗時はデフォルト 1 件を返す。"""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [
            CallTemplate(
                style=item["style"],
                lyrics_template=item["lyrics_template"],
                duration_sec=int(item["duration_sec"]),
            )
            for item in raw
        ]
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
        log.warning("call_prompts.json load failed (%s); using default", e)
        return [_DEFAULT_TEMPLATE]


def _detect_format(data: bytes) -> str:
    if len(data) < 4:
        return "unknown"
    if data[:4] == b"RIFF":
        return "wav"
    if data[:4] == b"OggS":
        return "ogg"
    if data[:3] == b"ID3":
        return "mp3"
    if len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return "mp3"
    return "unknown"


class CallPlayer:
    def __init__(
        self,
        lyria: LyriaService,
        audio: AudioService,
        templates: list[CallTemplate],
        max_workers: int = 4,
        play_wait_sec: float = 1.5,
    ) -> None:
        self._lyria = lyria
        self._audio = audio
        self._templates = templates or [_DEFAULT_TEMPLATE]
        self._max_workers = max_workers
        self._play_wait = play_wait_sec
        self._executor: ThreadPoolExecutor | None = None
        self._futures: dict[int, Future] = {}
        self._tmp_files: list[Path] = []

    def prefetch(self, players: list[Player]) -> None:
        """全員分の生成をバックグラウンドで開始。即 return。"""
        self.clear()
        if not players:
            return
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        for p in players:
            tmpl = random.choice(self._templates)
            self._futures[p.id] = self._executor.submit(self._generate_one, p.name, tmpl)

    def play(self, player: Player) -> bool:
        """プレイヤーに対応する Sound を再生。完了済 or 短時間待機。"""
        future = self._futures.get(player.id)
        if future is None:
            log.warning("call play: no future for player %s (id=%s)", player.name, player.id)
            return False
        try:
            result = future.result(timeout=self._play_wait)
        except Exception as e:
            log.warning(
                "call play wait failed for %s: %s (%s)",
                player.name,
                e or "timeout",
                type(e).__name__,
            )
            return False
        if result is None:
            log.warning("call play: result is None for %s", player.name)
            return False
        try:
            if isinstance(result, tuple) and result[0] == "file":
                pygame.mixer.music.load(str(result[1]))
                pygame.mixer.music.set_volume(1.0)
                pygame.mixer.music.play()
                log.info("call play: started mixer.music for %s (%s)", player.name, result[1])
            else:
                # pygame.mixer.Sound
                result.set_volume(1.0)
                result.play()
                log.info("call play: started Sound for %s", player.name)
            return True
        except Exception as e:
            log.warning("call play exec failed for %s: %s", player.name, e)
            return False

    def clear(self) -> None:
        """Future をキャンセルし、状態をリセット。"""
        for f in self._futures.values():
            f.cancel()
        self._futures.clear()
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None
        for p in self._tmp_files:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass
        self._tmp_files.clear()

    def _generate_one(self, name: str, template: CallTemplate) -> Playable | None:
        audio_bytes = self._lyria.synthesize_call(name, template)
        if not audio_bytes:
            log.warning("call generate: lyria returned no bytes for %s", name)
            return None
        fmt = _detect_format(audio_bytes)
        log.info(
            "call generate: got %d bytes (format=%s) for %s",
            len(audio_bytes),
            fmt,
            name,
        )
        # WAV/OGG は Sound でロードを試す
        if fmt in ("wav", "ogg"):
            try:
                return pygame.mixer.Sound(io.BytesIO(audio_bytes))
            except Exception as e:
                log.warning("Sound(BytesIO) failed for %s: %s, falling back to tempfile", name, e)
        # MP3 / unknown / Sound 失敗 → 一時ファイルに書いて mixer.music で再生する
        try:
            ext = fmt if fmt in ("mp3", "wav", "ogg") else "mp3"
            tmp = Path(tempfile.mkstemp(suffix=f".{ext}", prefix="nomiboy-call-")[1])
            tmp.write_bytes(audio_bytes)
            self._tmp_files.append(tmp)
            return ("file", tmp)
        except Exception as e:
            log.warning("tempfile write failed for %s: %s", name, e)
            return None
