from nomiboy.core.widgets.keyboard import ROMAJI_ROWS, VirtualKeyboard


def test_rows_are_romaji():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    assert kb.rows() == ROMAJI_ROWS
    assert kb.rows()[0] == "qwertyuiop"


def test_append_romaji_converts_to_hiragana():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    for c in "tarou":
        kb.append(c)
    assert kb.text == "たろう"
    assert kb.pending == ""


def test_append_keeps_pending_until_resolvable():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    kb.append("k")
    assert kb.text == ""
    assert kb.pending == "k"
    kb.append("a")
    assert kb.text == "か"
    assert kb.pending == ""


def test_max_len_in_hiragana_chars():
    kb = VirtualKeyboard(area=(0, 60, 480, 260), max_len=3)
    for c in "tarouko":
        kb.append(c)
    # たろう (3 文字) で打ち止め、その後の入力は無視
    assert kb.text == "たろう"
    assert kb.pending == ""


def test_backspace_removes_pending_first_then_text():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    kb.append("k")
    kb.append("a")  # text=か pending=""
    kb.append("k")  # pending=k
    kb.backspace()  # pending クリア
    assert kb.text == "か"
    assert kb.pending == ""
    kb.backspace()  # text の最後尾削除
    assert kb.text == ""


def test_clear_resets_text_and_pending():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    kb.append("k")
    kb.append("a")
    kb.append("n")
    kb.clear()
    assert kb.text == ""
    assert kb.pending == ""


def test_commit_flushes_trailing_n():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    for c in "kan":
        kb.append(c)
    assert kb.text == "か"
    assert kb.pending == "n"
    result = kb.commit()
    assert result == "かん"
    assert kb.text == "かん"
    assert kb.pending == ""


def test_display_includes_pending():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    kb.append("k")
    kb.append("a")
    kb.append("s")
    assert kb.display == "かs"
