"""グローバル MenuOverlay の単体テスト。"""
from __future__ import annotations

from unittest.mock import MagicMock

from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.menu_overlay import MenuOverlay


class _StubScene:
    pass


class _NoMenuScene:
    show_menu = False


def _tap(x: int, y: int) -> InputEvent:
    return InputEvent(kind=InputKind.TAP, x=x, y=y)


def _release(x: int, y: int) -> InputEvent:
    return InputEvent(kind=InputKind.RELEASE, x=x, y=y)


def _overlay() -> tuple[MenuOverlay, MagicMock, MagicMock]:
    sm = MagicMock()
    ctx = MagicMock()
    return MenuOverlay(sm=sm, ctx=ctx), sm, ctx


def test_is_visible_for_default_scene():
    m, _, _ = _overlay()
    assert m.is_visible_for(_StubScene()) is True


def test_is_visible_for_no_menu_scene():
    m, _, _ = _overlay()
    assert m.is_visible_for(_NoMenuScene()) is False


def test_is_visible_for_none_scene():
    m, _, _ = _overlay()
    assert m.is_visible_for(None) is False


def test_tap_on_menu_button_opens_menu():
    m, _, _ = _overlay()
    assert m.is_open is False
    cx, cy = m.menu_button_rect.center
    consumed = m.handle_event(_tap(cx, cy))
    assert consumed is True
    assert m.is_open is True


def test_tap_outside_menu_button_when_closed_returns_false():
    m, _, _ = _overlay()
    consumed = m.handle_event(_tap(100, 100))
    assert consumed is False
    assert m.is_open is False


def test_tap_outside_popup_when_open_closes_menu():
    m, _, _ = _overlay()
    m._open = True  # type: ignore[attr-defined]
    # 左下、ポップアップ外
    consumed = m.handle_event(_tap(20, 20))
    assert consumed is True
    assert m.is_open is False


def test_tap_back_to_title_resets_and_clears_players():
    m, sm, ctx = _overlay()
    m._open = True  # type: ignore[attr-defined]
    cx, cy = m.back_to_title_rect.center
    consumed = m.handle_event(_tap(cx, cy))
    assert consumed is True
    assert m.is_open is False
    ctx.players.clear.assert_called_once()
    sm.reset_to.assert_called_once()
    pushed = sm.reset_to.call_args.args[0]
    assert pushed.__class__.__name__ == "TitleScene"


def test_tap_select_games_resets_and_preserves_players():
    m, sm, ctx = _overlay()
    m._open = True  # type: ignore[attr-defined]
    cx, cy = m.select_games_rect.center
    consumed = m.handle_event(_tap(cx, cy))
    assert consumed is True
    assert m.is_open is False
    ctx.players.clear.assert_not_called()
    sm.reset_to.assert_called_once()
    pushed = sm.reset_to.call_args.args[0]
    assert pushed.__class__.__name__ == "GameSelectScene"


def test_non_tap_event_returns_false_when_closed():
    m, _, _ = _overlay()
    assert m.handle_event(_release(100, 100)) is False


def test_tap_on_menu_button_again_toggles_closed():
    m, _, _ = _overlay()
    cx, cy = m.menu_button_rect.center
    m.handle_event(_tap(cx, cy))
    assert m.is_open is True
    # 開いてる状態で MENU をもう一度押すと閉じる
    m.handle_event(_tap(cx, cy))
    assert m.is_open is False
