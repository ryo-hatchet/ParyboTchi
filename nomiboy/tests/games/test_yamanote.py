"""AI 山手線シーンの基本テスト。"""
from __future__ import annotations

from unittest.mock import MagicMock

from nomiboy.games.yamanote import YamanoteScene, YamanoteState
from nomiboy.stores.player_store import Player


def _ctx(players_count: int):
    ctx = MagicMock()
    ctx.players.players = [
        Player(id=i, name=f"P{i}", color=(i * 50, 100, 200)) for i in range(players_count)
    ]
    ctx.online = False
    ctx.assets.font.return_value = MagicMock()
    return ctx


def _scene(players_count: int = 2) -> tuple[YamanoteScene, MagicMock]:
    scene = YamanoteScene(scene_manager=MagicMock())
    ctx = _ctx(players_count)
    scene.on_enter(ctx)
    return scene, ctx


def test_on_enter_picks_topic_and_starts_prompt():
    scene, _ = _scene()
    assert scene._state == YamanoteState.PROMPT
    assert scene._topic  # 非空
    assert scene._round_count == 0


def test_ok_judgment_appends_history_and_advances():
    scene, _ = _scene(3)
    scene._current_answer = "麻婆豆腐"
    scene._on_judged(True, "")
    assert scene._state == YamanoteState.OK_REVEAL
    assert "麻婆豆腐" in scene._history


def test_ng_judgment_sets_loser():
    scene, _ = _scene(2)
    scene._current_player_idx = 1
    scene._current_answer = "つまらん回答"
    scene._on_judged(False, "真面目すぎ")
    assert scene._state == YamanoteState.NG_REVEAL
    assert scene._loser is not None
    assert scene._loser.name == "P1"
    assert scene._ai_comment == "真面目すぎ"


def test_advance_player_rotates():
    scene, _ = _scene(3)
    assert scene._current_player_idx == 0
    scene._advance_player()
    assert scene._current_player_idx == 1
    assert scene._round_count == 1
    assert scene._state == YamanoteState.PROMPT


def test_advance_player_ends_after_max_rounds():
    scene, _ = _scene(2)
    scene._max_rounds = 2
    scene._advance_player()
    scene._advance_player()
    assert scene._state == YamanoteState.DONE


def test_empty_answer_returns_to_prompt():
    scene, _ = _scene(2)
    scene._on_input_confirmed("   ")  # 空白のみ
    assert scene._state == YamanoteState.PROMPT
