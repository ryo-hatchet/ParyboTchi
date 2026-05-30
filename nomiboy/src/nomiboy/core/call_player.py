"""ドリンクコール再生サービス。ゲーム開始時に全員分をプリフェッチし、負け確定時に再生する。"""
from __future__ import annotations

import io
import json
import logging
import random
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

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
        self._futures: dict[int, Future[pygame.mixer.Sound | None]] = {}

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
            return False
        try:
            sound = future.result(timeout=self._play_wait)
        except Exception as e:
            log.warning(
                "call play wait failed for %s: %s (%s)",
                player.name,
                e or "timeout",
                type(e).__name__,
            )
            return False
        if sound is None:
            return False
        sound.play()
        return True

    def clear(self) -> None:
        """Future をキャンセルし、状態をリセット。"""
        for f in self._futures.values():
            f.cancel()
        self._futures.clear()
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None

    def _generate_one(self, name: str, template: CallTemplate) -> "pygame.mixer.Sound | None":
        wav_bytes = self._lyria.synthesize_call(name, template)
        if not wav_bytes:
            return None
        try:
            return pygame.mixer.Sound(io.BytesIO(wav_bytes))
        except Exception as e:
            log.warning("Sound load failed for %s: %s", name, e)
            return None
