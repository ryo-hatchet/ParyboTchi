"""Gemini Lyria 3 サービス。人名入りコール曲を生成する。

API キー未設定 / disabled / ネット失敗時はすべて None を返す。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class CallTemplate:
    style: str
    lyrics_template: str  # "{name}" を含む
    duration_sec: int


class LyriaService:
    def __init__(
        self,
        api_key: str | None,
        model: str = "lyria-3-pro-preview",
        timeout_sec: float = 60.0,
        disabled: bool = False,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_sec
        self._disabled = disabled

    def synthesize_call(self, player_name: str, template: CallTemplate) -> bytes | None:
        if self._disabled or not self._api_key:
            return None
        try:
            return self._generate(player_name, template)
        except Exception as e:
            log.warning("Lyria generation failed for %s: %s", player_name, e)
            return None

    def _generate(self, player_name: str, template: CallTemplate) -> bytes | None:
        """Task 4 で実装。"""
        raise NotImplementedError
