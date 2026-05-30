"""Gemini Flash で歌詞を生成するサービス。

カラオケゲームのために、ジャンルとプレイヤー名リスト + コール度から
Lyrics: タグ付きの歌詞テキストを返す。
"""
from __future__ import annotations

import logging

from google import genai
from google.genai import types

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "あなたは飲み会用カラオケソングの作詞家です。"
    "指定されたジャンルで、出演者の名前を「コール度」に応じて不均衡に登場させる歌詞を作ってください。"
    "[Intro][Verse 1][Chorus][Verse 2][Outro] の構成で、[Chorus] に必ず「乾杯！」のコールを入れます。"
    "曲の長さは 20 秒程度を想定。飲み会らしいノリで、できる限り煽り口調で。"
    "返答は以下の形式で歌詞のみ:\n\nLyrics:\n[Intro]\n..."
)


def _default_lyrics(genre: str, names: list[str]) -> str:
    """API 失敗時のフォールバック歌詞。"""
    name_line = "、".join(names)
    return (
        "Lyrics:\n"
        "[Intro]\n"
        f"今夜は {genre} で乾杯だ\n"
        "[Verse 1]\n"
        f"{name_line} 集まれ\n"
        "飲み干せ 飲み干せ\n"
        "[Chorus]\n"
        "乾杯！ 乾杯！ みんなで乾杯！\n"
        f"{names[0] if names else 'みんな'} も飲んで\n"
        "[Verse 2]\n"
        "夜は長い 朝まで歌え\n"
        "[Outro]\n"
        "今宵も最高！\n"
    )


class LyricsService:
    def __init__(
        self,
        api_key: str | None,
        model: str = "gemini-3.5-flash",
        timeout_sec: float = 15.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_sec

    def generate_song_lyrics(
        self,
        genre: str,
        emphasis: dict[str, float],
    ) -> str | None:
        """ジャンルとコール度から歌詞を生成。失敗時 None。"""
        if not self._api_key or not emphasis:
            return None
        try:
            return self._generate(genre, emphasis)
        except Exception as e:
            log.warning("Lyrics generation failed: %s (%s)", e, type(e).__name__)
            return None

    def _generate(self, genre: str, emphasis: dict[str, float]) -> str | None:
        client = genai.Client(api_key=self._api_key)
        names_block = "\n".join(
            f"- {n}: コール度 {w:.1f}" for n, w in emphasis.items()
        )
        prompt = (
            f"{_SYSTEM_PROMPT}\n\n"
            f"ジャンル: {genre}\n\n"
            f"出演者:\n{names_block}\n"
        )
        log.info("Lyrics request genre=%s names=%d", genre, len(emphasis))
        response = client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT"],
                temperature=1.0,
            ),
        )
        if not response.candidates:
            log.warning("Lyrics response has no candidates")
            return None
        parts = response.candidates[0].content.parts if response.candidates[0].content else []
        for part in parts:
            text = getattr(part, "text", None)
            if text and "Lyrics" in text:
                log.info("Lyrics generated: %d chars", len(text))
                return text
        # 何か返ってきていれば最初の text を採用
        for part in parts:
            text = getattr(part, "text", None)
            if text:
                return text
        return None
