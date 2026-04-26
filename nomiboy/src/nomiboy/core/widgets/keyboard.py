"""仮想キーボード。50音/カナ/英数字をタブで切替。"""
from __future__ import annotations

from enum import Enum

HIRAGANA_ROWS = [
    "あいうえお",
    "かきくけこ",
    "さしすせそ",
    "たちつてと",
    "なにぬねの",
    "はひふへほ",
    "まみむめも",
    "やゆよわん",
    "らりるれろ",
    "がぎぐげご",
    "ざじずぜぞ",
    "だぢづでど",
    "ばびぶべぼ",
    "ぱぴぷぺぽ",
]

KATAKANA_ROWS = [
    "アイウエオ",
    "カキクケコ",
    "サシスセソ",
    "タチツテト",
    "ナニヌネノ",
    "ハヒフヘホ",
    "マミムメモ",
    "ヤユヨワン",
    "ラリルレロ",
    "ガギグゲゴ",
    "ザジズゼゾ",
    "ダヂヅデド",
    "バビブベボ",
    "パピプペポ",
]

ALPHANUM_ROWS = [
    "1234567890",
    "abcdefghij",
    "klmnopqrst",
    "uvwxyz",
]


class KeyboardMode(Enum):
    HIRAGANA = "hira"
    KATAKANA = "kata"
    ALPHANUM = "alnum"


class VirtualKeyboard:
    def __init__(self, area: tuple[int, int, int, int], max_len: int = 8) -> None:
        self.area = area
        self.max_len = max_len
        self.text: str = ""
        self.mode: KeyboardMode = KeyboardMode.HIRAGANA

    def rows(self) -> list[str]:
        if self.mode == KeyboardMode.HIRAGANA:
            return HIRAGANA_ROWS
        if self.mode == KeyboardMode.KATAKANA:
            return KATAKANA_ROWS
        return ALPHANUM_ROWS

    def switch_mode(self) -> None:
        order = [KeyboardMode.HIRAGANA, KeyboardMode.KATAKANA, KeyboardMode.ALPHANUM]
        self.mode = order[(order.index(self.mode) + 1) % len(order)]

    def append(self, ch: str) -> None:
        if len(self.text) >= self.max_len:
            return
        self.text += ch

    def backspace(self) -> None:
        self.text = self.text[:-1]

    def clear(self) -> None:
        self.text = ""
