"""Gemini TTS サービス。永続キャッシュ + 例外吸収。"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from nomiboy.config import TTS_CACHE_DIR

log = logging.getLogger(__name__)


class TTSService:
    def __init__(
        self,
        api_key: str | None,
        cache_dir: Path = TTS_CACHE_DIR,
        timeout_sec: float = 5.0,
    ) -> None:
        self._api_key = api_key
        self._cache_dir = cache_dir
        self._timeout = timeout_sec
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def cache_key(self, text: str, voice: str = "default") -> str:
        h = hashlib.sha1(f"{voice}|{text}".encode("utf-8")).hexdigest()
        return h[:16]

    def speak(self, text: str, voice: str = "default") -> Path | None:
        try:
            key = self.cache_key(text, voice)
            path = self._cache_dir / f"{key}.wav"
            if path.exists():
                return path
            if not self._api_key:
                return None
            wav_bytes = self._synthesize(text, voice)
            if wav_bytes is None:
                return None
            path.write_bytes(wav_bytes)
            return path
        except Exception as e:
            log.warning("TTS failed: %s", e)
            return None

    def _synthesize(self, text: str, voice: str) -> bytes | None:
        """実際の Gemini API 呼び出し。Task 29 で詰める。"""
        return None
