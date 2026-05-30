"""ローマ字 → ひらがな変換ロジック。

入力は逐次 1 文字。pending バッファに溜めながら、確定できる分だけ
ひらがなに変換して `text` に追加する。
"""
from __future__ import annotations


_TABLE: dict[str, str] = {
    # 母音
    "a": "あ", "i": "い", "u": "う", "e": "え", "o": "お",
    # k 行
    "ka": "か", "ki": "き", "ku": "く", "ke": "け", "ko": "こ",
    "kya": "きゃ", "kyu": "きゅ", "kyo": "きょ",
    # s 行
    "sa": "さ", "shi": "し", "si": "し", "su": "す", "se": "せ", "so": "そ",
    "sha": "しゃ", "shu": "しゅ", "sho": "しょ",
    "sya": "しゃ", "syu": "しゅ", "syo": "しょ",
    # t 行
    "ta": "た", "chi": "ち", "ti": "ち", "tsu": "つ", "tu": "つ", "te": "て", "to": "と",
    "cha": "ちゃ", "chu": "ちゅ", "cho": "ちょ",
    "tya": "ちゃ", "tyu": "ちゅ", "tyo": "ちょ",
    # n 行
    "na": "な", "ni": "に", "nu": "ぬ", "ne": "ね", "no": "の",
    "nya": "にゃ", "nyu": "にゅ", "nyo": "にょ",
    "n": "ん",  # 末尾フラッシュ用
    # h 行
    "ha": "は", "hi": "ひ", "fu": "ふ", "hu": "ふ", "he": "へ", "ho": "ほ",
    "hya": "ひゃ", "hyu": "ひゅ", "hyo": "ひょ",
    "fa": "ふぁ", "fi": "ふぃ", "fe": "ふぇ", "fo": "ふぉ",
    # m 行
    "ma": "ま", "mi": "み", "mu": "む", "me": "め", "mo": "も",
    "mya": "みゃ", "myu": "みゅ", "myo": "みょ",
    # y 行
    "ya": "や", "yu": "ゆ", "yo": "よ",
    # r 行
    "ra": "ら", "ri": "り", "ru": "る", "re": "れ", "ro": "ろ",
    "rya": "りゃ", "ryu": "りゅ", "ryo": "りょ",
    # w 行
    "wa": "わ", "wo": "を", "wi": "うぃ", "we": "うぇ",
    # 濁音 g
    "ga": "が", "gi": "ぎ", "gu": "ぐ", "ge": "げ", "go": "ご",
    "gya": "ぎゃ", "gyu": "ぎゅ", "gyo": "ぎょ",
    # 濁音 z / j
    "za": "ざ", "ji": "じ", "zi": "じ", "zu": "ず", "ze": "ぜ", "zo": "ぞ",
    "ja": "じゃ", "ju": "じゅ", "jo": "じょ",
    "jya": "じゃ", "jyu": "じゅ", "jyo": "じょ",
    # 濁音 d
    "da": "だ", "di": "ぢ", "du": "づ", "de": "で", "do": "ど",
    # 濁音 b
    "ba": "ば", "bi": "び", "bu": "ぶ", "be": "べ", "bo": "ぼ",
    "bya": "びゃ", "byu": "びゅ", "byo": "びょ",
    # 半濁音 p
    "pa": "ぱ", "pi": "ぴ", "pu": "ぷ", "pe": "ぺ", "po": "ぽ",
    "pya": "ぴゃ", "pyu": "ぴゅ", "pyo": "ぴょ",
    # 長音
    "-": "ー",
}

# 促音 (小さい っ) 対象の子音
_DOUBLE_CONSONANTS = frozenset("kstpbdgzjmhfr")


def _is_prefix_of_longer(pending: str) -> bool:
    """pending が他のもっと長いキーの接頭辞か。"""
    for k in _TABLE:
        if k != pending and k.startswith(pending):
            return True
    return False


def step(text: str, pending: str, ch: str) -> tuple[str, str]:
    """pending に ch を 1 文字追加し、確定できる分を text に変換して返す。

    Returns (new_text, new_pending).
    """
    pending = pending + ch
    while pending:
        # 促音: 子音 + 同じ子音 (len==2) → 3文字目を待機（タップ二重発火対策）
        if (
            len(pending) == 2
            and pending[0] == pending[1]
            and pending[0] in _DOUBLE_CONSONANTS
        ):
            return text, pending
        # 促音: 子音 + 同じ子音 + 何か（len>=3）→ 小さい っ + 残りで再評価
        if (
            len(pending) >= 3
            and pending[0] == pending[1]
            and pending[0] in _DOUBLE_CONSONANTS
        ):
            text += "っ"
            pending = pending[1:]
            continue

        # 撥音: "n" + 母音/y 以外（= 子音 or n）→ 単独 n を ん として確定
        if (
            len(pending) >= 2
            and pending[0] == "n"
            and pending[1] not in "aiueoy"
        ):
            text += "ん"
            pending = pending[1:]
            continue

        # 完全一致 + さらに長いキーの接頭辞でなければ確定
        if pending in _TABLE and not _is_prefix_of_longer(pending):
            text += _TABLE[pending]
            pending = ""
            continue

        # まだ更に長くなる可能性があれば待機
        if _is_prefix_of_longer(pending):
            return text, pending

        # 完全一致でも接頭辞でもない: 先頭から最長一致を切り出す
        consumed = 0
        for length in (3, 2, 1):
            if length < len(pending) and pending[:length] in _TABLE:
                text += _TABLE[pending[:length]]
                pending = pending[length:]
                consumed = length
                break
        if consumed == 0:
            # どうしようもない先頭文字を捨てる
            pending = pending[1:]

    return text, ""


def flush(text: str, pending: str) -> tuple[str, str]:
    """確定操作時の最終フラッシュ。pending に残っているものを可能なら変換。"""
    while pending:
        # 促音残り (例: "tt") → っ
        if (
            len(pending) >= 2
            and pending[0] == pending[1]
            and pending[0] in _DOUBLE_CONSONANTS
        ):
            text += "っ"
            pending = pending[1:]
            continue
        if pending in _TABLE:
            text += _TABLE[pending]
            pending = ""
            break
        # 先頭から最長一致
        consumed = 0
        for length in (3, 2, 1):
            if length <= len(pending) and pending[:length] in _TABLE:
                text += _TABLE[pending[:length]]
                pending = pending[length:]
                consumed = length
                break
        if consumed == 0:
            pending = pending[1:]
    return text, ""
