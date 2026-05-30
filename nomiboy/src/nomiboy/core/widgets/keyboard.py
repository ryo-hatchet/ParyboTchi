"""仮想ローマ字キーボード。タップで a-z を入力し内部でひらがなに変換する。"""
from __future__ import annotations

from nomiboy.core.widgets.romaji import flush as romaji_flush
from nomiboy.core.widgets.romaji import step as romaji_step

# QWERTY 風配列（小文字、4 行）
ROMAJI_ROWS = [
    "qwertyuiop",
    "asdfghjkl-",
    "zxcvbnm",
]


class VirtualKeyboard:
    """ローマ字をタップで入力 → ひらがなに自動変換する仮想キーボード。"""

    def __init__(self, area: tuple[int, int, int, int], max_len: int = 8) -> None:
        self.area = area
        self.max_len = max_len
        self.text: str = ""       # 確定済ひらがな
        self.pending: str = ""    # 未確定ローマ字

    def rows(self) -> list[str]:
        return ROMAJI_ROWS

    @property
    def display(self) -> str:
        """画面に出す文字列 = 確定 + 未確定。"""
        return self.text + self.pending

    def append(self, ch: str) -> None:
        if len(self.text) >= self.max_len and not self.pending:
            return
        new_text, new_pending = romaji_step(self.text, self.pending, ch)
        # max_len 超過した場合は確定分を切り詰める
        if len(new_text) > self.max_len:
            return
        self.text = new_text
        self.pending = new_pending

    def backspace(self) -> None:
        if self.pending:
            self.pending = self.pending[:-1]
            return
        if self.text:
            self.text = self.text[:-1]

    def clear(self) -> None:
        self.text = ""
        self.pending = ""

    def commit(self) -> str:
        """確定操作。pending を可能な限りフラッシュして text を返す。"""
        self.text, self.pending = romaji_flush(self.text, self.pending)
        if len(self.text) > self.max_len:
            self.text = self.text[: self.max_len]
        return self.text
