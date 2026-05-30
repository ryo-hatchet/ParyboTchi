"""Gemini Lyria 3 サービス。人名入りコール曲を生成する。

API キー未設定 / disabled / ネット失敗時はすべて None を返す。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from google import genai
from google.genai import types

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
        prompt = self._build_prompt(player_name, template)
        log.info("Lyria request for %s, prompt: %s", player_name, prompt[:120])
        client = genai.Client(api_key=self._api_key)
        response = client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
            ),
        )
        if not response.candidates:
            finish_info = getattr(response, "prompt_feedback", None)
            log.warning(
                "Lyria response has no candidates for %s, prompt_feedback=%s",
                player_name,
                finish_info,
            )
            return None
        cand = response.candidates[0]
        finish_reason = getattr(cand, "finish_reason", None)
        log.info("Lyria candidate finish_reason=%s for %s", finish_reason, player_name)
        parts = cand.content.parts if cand.content else []
        for i, part in enumerate(parts):
            inline = getattr(part, "inline_data", None)
            text = getattr(part, "text", None)
            mime = getattr(inline, "mime_type", None) if inline else None
            data = getattr(inline, "data", None) if inline else None
            data_len = len(data) if data else 0
            log.info(
                "Lyria part[%d] mime=%s data_len=%d text=%s",
                i,
                mime,
                data_len,
                (text or "")[:80],
            )
            if data:
                return data if isinstance(data, bytes) else bytes(data)
        return None

    @staticmethod
    def _build_prompt(player_name: str, template: CallTemplate) -> str:
        lyrics = template.lyrics_template.replace("{name}", player_name)
        return (
            f"{template.style}\n"
            f"Duration: about {template.duration_sec} seconds.\n\n"
            f"{lyrics}"
        )
