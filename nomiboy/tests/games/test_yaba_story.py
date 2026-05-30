"""ヤバ物語シーンの基本テスト。"""
from __future__ import annotations

from unittest.mock import MagicMock

from nomiboy.games.yaba_story import YabaStoryScene, YabaStoryState, _wrap_text
from nomiboy.stores.player_store import Player


def test_wrap_text_breaks_at_max_chars():
    text = "あいうえおかきくけこさしすせそ"
    lines = _wrap_text(text, 5)
    assert lines == ["あいうえお", "かきくけこ", "さしすせそ"]


def test_wrap_text_respects_explicit_newlines():
    lines = _wrap_text("abc\nxyz", 10)
    assert lines == ["abc", "xyz"]


def _scene_with_result(result):
    scene = YabaStoryScene(scene_manager=MagicMock())
    ctx = MagicMock()
    ctx.players.players = [
        Player(id=0, name="たろう", color=(255, 0, 0)),
        Player(id=1, name="はなこ", color=(0, 255, 0)),
    ]
    ctx.lyrics.generate_yaba_story.return_value = result
    ctx.assets.font.return_value = MagicMock()
    scene.on_enter(ctx)
    scene._future.result()  # type: ignore[union-attr]
    scene._update_loading()
    return scene


def test_loading_to_story_with_success():
    scene = _scene_with_result(("今夜の物語", "たろう", "派手すぎた"))
    assert scene._state == YabaStoryState.STORY
    assert scene._loser_name == "たろう"
    assert scene._reason == "派手すぎた"


def test_loading_to_story_with_failure_uses_fallback():
    scene = _scene_with_result(None)
    assert scene._state == YabaStoryState.STORY
    assert scene._loser_name in ["たろう", "はなこ"]
    assert "コケた" in scene._reason or len(scene._reason) > 0


def test_find_loser_returns_matching_player():
    scene = _scene_with_result(("ストーリー", "たろう", "理由"))
    loser = scene._find_loser()
    assert loser is not None
    assert loser.name == "たろう"


def test_find_loser_partial_match():
    scene = _scene_with_result(("ストーリー", "たろうさん", "理由"))
    loser = scene._find_loser()
    assert loser is not None
    assert loser.name == "たろう"


def test_reveal_transitions_state():
    scene = _scene_with_result(("ストーリー", "たろう", "理由"))
    scene._reveal()
    assert scene._state == YabaStoryState.REVEAL


def test_error_when_no_players():
    scene = YabaStoryScene(scene_manager=MagicMock())
    ctx = MagicMock()
    ctx.players.players = []
    ctx.assets.font.return_value = MagicMock()
    scene.on_enter(ctx)
    assert scene._state == YabaStoryState.ERROR
