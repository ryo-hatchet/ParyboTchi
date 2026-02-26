"""ParyboTchi - Gemini API 曲解説モジュール"""

import threading
from google import genai

from config import GEMINI_API_KEY, GEMINI_MODEL


class SongDescriber:
    """Gemini APIを使って曲の解説を生成するクラス"""

    def __init__(self):
        self.is_busy = False
        self.result = None  # 解説テキスト (str) or None
        self.error = None
        self._thread = None
        self._client = genai.Client(api_key=GEMINI_API_KEY)

    def describe(self, title, artist):
        """曲の解説を別スレッドで取得する"""
        if self.is_busy:
            return
        self.result = None
        self.error = None
        self.is_busy = True
        self._thread = threading.Thread(
            target=self._run, args=(title, artist), daemon=True
        )
        self._thread.start()

    def _run(self, title, artist):
        """Gemini APIを呼び出す（別スレッド）"""
        try:
            prompt = (
                f"「{title} / {artist}」という曲について、"
                "100文字以内で簡潔に解説してください。"
                "曲の特徴や背景を端的に伝えてください。"
            )
            response = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            self.result = response.text.strip()
            print(f"[GEMINI] 解説取得成功: {self.result}")
        except Exception as e:
            print(f"[GEMINI] エラー: {e}")
            self.error = str(e)
        finally:
            self.is_busy = False
