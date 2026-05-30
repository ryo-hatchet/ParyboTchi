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


_MINORITY_PROMPT = (
    "あなたは飲み会用 YES/NO クイズの問題作成者です。"
    "以下のルールで {n} 個の質問を作ってください:\n"
    "- 飲み会で答えやすい二択（YES / NO で答えられる）\n"
    "- ちょっと際どいけど嫌悪感ない範囲、しっとり系よりも盛り上がる系\n"
    "- 「私は XX 派」「私は XX したことある」「私は XX 派」のような自己申告型\n"
    "- 答えが分かれそうなものを選ぶ\n"
    "- 各質問は 30 文字以内\n"
    "- 句読点や記号無しで簡潔に\n\n"
    "返答は質問のみを 1 行ずつ、{n} 行で。番号や記号も付けない。"
)


_DEFAULT_MINORITY_QUESTIONS = [
    "ビール派？ (YES) / 焼酎派？ (NO)",
    "カラオケで本気で歌う？",
    "朝まで飲んだことある？",
    "酔うとよく喋るタイプ？",
    "二日酔いに弱い？",
]


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

    def judge_yamanote_answer(
        self, topic: str, answer: str, history: list[str]
    ) -> tuple[bool, str] | None:
        """山手線ゲーム判定。answer がお題に合っているか + 面白いか。

        - ok=True: お題に合致、つまらなくない
        - ok=False: ルール違反、過去回答とかぶり、または「つまらん」
        comment は 20 字以内の煽り口調。

        失敗時 None。
        """
        if not self._api_key:
            return None
        try:
            client = genai.Client(api_key=self._api_key)
            hist_block = "\n".join(f"- {h}" for h in history) if history else "（なし）"
            prompt = (
                "あなたは飲み会の山手線ゲームの審判です。\n\n"
                f"お題: 「{topic}」\n"
                f"既出の回答:\n{hist_block}\n\n"
                f"プレイヤーの回答: 「{answer}」\n\n"
                "判定ルール:\n"
                "- お題に合致しているか\n"
                "- 既出と被ってないか\n"
                "- お酒の場として「面白さ/勢い」があるか\n"
                "上記すべて OK なら ok=true。\n"
                "ルール違反/被り/真面目すぎ/つまらないなら ok=false。\n"
                "comment は 20 字以内、煽り口調の日本語。\n\n"
                "JSON で返答（コードブロック禁止、生 JSON のみ）:\n"
                '{"ok": true|false, "comment": "理由"}'
            )
            response = client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT"],
                    temperature=0.8,
                    response_mime_type="application/json",
                ),
            )
            if not response.candidates:
                return None
            text = ""
            parts = response.candidates[0].content.parts if response.candidates[0].content else []
            for part in parts:
                t = getattr(part, "text", None)
                if t:
                    text += t
            import json as _json

            data = _json.loads(text)
            ok = bool(data.get("ok", True))
            comment = str(data.get("comment", "")).strip()[:24]
            return (ok, comment)
        except Exception as e:
            log.warning("Yamanote judge failed: %s", e)
            return None

    def generate_yaba_story(self, names: list[str]) -> tuple[str, str, str] | None:
        """全員主役のヤバ物語 + 飲む人 + 理由を返す。失敗時 None。

        戻り値: (本文, 飲む人の名前, 理由 ≤30字)
        """
        if not self._api_key or not names:
            return None
        try:
            client = genai.Client(api_key=self._api_key)
            names_block = "\n".join(f"- {n}" for n in names)
            prompt = (
                "あなたは飲み会の語り部です。以下のメンバーを全員登場させる "
                "短編ヤバストーリーを作ってください。\n"
                f"メンバー:\n{names_block}\n\n"
                "ルール:\n"
                "- 200 字以内の短編\n"
                "- 居酒屋・宴会・カラオケ等の盛り上がるシーン\n"
                "- 全員必ず登場し、それぞれ違う行動をする\n"
                "- 最後に「この物語で一番ヤバいやつ」を 1 人だけ名指しで指名\n"
                "- 理由は 30 字以内、煽り口調で\n\n"
                "JSON で返答（コードブロック禁止、生 JSON のみ）:\n"
                '{"story": "本文…", "loser": "名前", "reason": "理由"}'
            )
            response = client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT"],
                    temperature=1.1,
                    response_mime_type="application/json",
                ),
            )
            if not response.candidates:
                return None
            text = ""
            parts = response.candidates[0].content.parts if response.candidates[0].content else []
            for part in parts:
                t = getattr(part, "text", None)
                if t:
                    text += t
            import json as _json

            data = _json.loads(text)
            story = str(data.get("story", "")).strip()
            loser = str(data.get("loser", "")).strip()
            reason = str(data.get("reason", "")).strip()
            if not story or not loser:
                return None
            return (story, loser, reason)
        except Exception as e:
            log.warning("Yaba story generation failed: %s", e)
            return None

    def generate_minority_questions(self, n: int = 5) -> list[str]:
        """YES/NO 質問を n 件生成。失敗時はデフォルトを返す。"""
        if not self._api_key:
            return list(_DEFAULT_MINORITY_QUESTIONS)
        try:
            client = genai.Client(api_key=self._api_key)
            prompt = _MINORITY_PROMPT.format(n=n)
            response = client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT"],
                    temperature=1.2,
                ),
            )
            if not response.candidates:
                return list(_DEFAULT_MINORITY_QUESTIONS)
            text = ""
            parts = response.candidates[0].content.parts if response.candidates[0].content else []
            for part in parts:
                t = getattr(part, "text", None)
                if t:
                    text += t
            lines = [
                ln.strip().lstrip("0123456789.- ").strip()
                for ln in text.splitlines()
                if ln.strip()
            ]
            lines = [ln for ln in lines if ln]
            if not lines:
                return list(_DEFAULT_MINORITY_QUESTIONS)
            return lines[:n] if len(lines) >= n else lines + _DEFAULT_MINORITY_QUESTIONS[: n - len(lines)]
        except Exception as e:
            log.warning("Minority questions generation failed: %s", e)
            return list(_DEFAULT_MINORITY_QUESTIONS)

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
