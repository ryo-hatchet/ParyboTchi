from nomiboy.core.widgets.keyboard import VirtualKeyboard, KeyboardMode


def test_starts_in_hiragana_mode():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    assert kb.mode == KeyboardMode.HIRAGANA


def test_switch_mode_cycles():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    kb.switch_mode()
    assert kb.mode == KeyboardMode.KATAKANA
    kb.switch_mode()
    assert kb.mode == KeyboardMode.ALPHANUM
    kb.switch_mode()
    assert kb.mode == KeyboardMode.HIRAGANA


def test_append_character_capped_at_max():
    kb = VirtualKeyboard(area=(0, 60, 480, 260), max_len=3)
    kb.text = "あい"
    kb.append("う")
    kb.append("え")
    assert kb.text == "あいう"


def test_backspace_removes_last_char():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    kb.text = "あいう"
    kb.backspace()
    assert kb.text == "あい"


def test_clear_resets_text():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    kb.text = "abc"
    kb.clear()
    assert kb.text == ""
