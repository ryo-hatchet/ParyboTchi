"""ローマ字 → ひらがな変換のテスト。"""
from __future__ import annotations

from nomiboy.core.widgets.romaji import flush, step


def _convert(romaji: str) -> tuple[str, str]:
    text, pending = "", ""
    for ch in romaji:
        text, pending = step(text, pending, ch)
    return text, pending


def test_simple_vowels():
    text, pending = _convert("aiueo")
    assert text == "あいうえお"
    assert pending == ""


def test_basic_consonant_vowel():
    text, _ = _convert("kakikukeko")
    assert text == "かきくけこ"


def test_shi_chi_tsu():
    text, _ = _convert("shichitsu")
    assert text == "しちつ"


def test_taro():
    text, _ = _convert("tarou")
    assert text == "たろう"


def test_hanako():
    text, _ = _convert("hanako")
    assert text == "はなこ"


def test_kyo_combo():
    text, _ = _convert("kyou")
    assert text == "きょう"


def test_double_consonant():
    text, _ = _convert("kitte")
    assert text == "きって"


def test_double_pp():
    text, _ = _convert("ippai")
    assert text == "いっぱい"


def test_n_at_end_needs_flush():
    text, pending = _convert("kan")
    # "kan" → か + n (待機)
    assert text == "か"
    assert pending == "n"
    # flush で ん 確定
    text, pending = flush(text, pending)
    assert text == "かん"
    assert pending == ""


def test_nn_immediately_kanji_n():
    text, _ = _convert("kanna")
    assert text == "かんな"


def test_n_before_vowel():
    text, _ = _convert("nani")
    assert text == "なに"


def test_sa_si_alt():
    text, _ = _convert("sisa")  # si → し
    assert text == "しさ"


def test_ji_dakuten():
    text, _ = _convert("jiji")
    assert text == "じじ"


def test_step_returns_pending_for_incomplete():
    text, pending = step("", "", "k")
    assert text == ""
    assert pending == "k"


def test_flush_with_invalid_pending_drops():
    text, pending = flush("", "x")
    assert text == ""
    assert pending == ""
