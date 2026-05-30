"""少数派 SHOT のロジックテスト。"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.games.minority import MinorityScene, MinorityState
from nomiboy.stores.player_store import Player


def _tap(x: int, y: int) -> InputEvent:
    return InputEvent(kind=InputKind.TAP, x=x, y=y)


def _players(n: int) -> list[Player]:
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    return [Player(id=i, name=f"P{i}", color=colors[i % 4]) for i in range(n)]


def _scene_with_questions(qs: list[str], n_players: int) -> tuple[MinorityScene, MagicMock]:
    scene = MinorityScene(scene_manager=MagicMock())
    ctx = MagicMock()
    ctx.players.players = _players(n_players)
    ctx.lyrics.generate_minority_questions.return_value = qs
    ctx.assets.font.return_value = MagicMock()
    scene.on_enter(ctx)
    # 同期的に future を完了させて questions を入手
    scene._future.result()  # type: ignore[union-attr]
    scene._update_loading()
    return scene, ctx


def test_loading_to_voting_transition():
    scene, _ = _scene_with_questions(["Q1", "Q2"], 2)
    assert scene._state == MinorityState.VOTING
    assert scene._questions == ["Q1", "Q2"]
    assert scene._round_idx == 0


def test_all_yes_means_unanimous_no_losers():
    scene, _ = _scene_with_questions(["Q1"], 3)
    # 全員 YES
    scene._cast_vote(True)
    scene._cast_vote(True)
    scene._cast_vote(True)
    assert scene._state == MinorityState.REVEAL
    assert scene._unanimous is True
    assert scene._losers_this_round == []


def test_minority_drinks():
    scene, _ = _scene_with_questions(["Q1"], 3)
    # 2 YES, 1 NO → NO が少数派
    scene._cast_vote(True)
    scene._cast_vote(True)
    scene._cast_vote(False)
    assert scene._state == MinorityState.REVEAL
    assert scene._unanimous is False
    assert len(scene._losers_this_round) == 1
    assert scene._losers_this_round[0].name == "P2"


def test_tie_picks_one_side_as_minority():
    """2 対 2 の場合は yes_n <= no_n のロジックで yes_ids が選ばれる。"""
    scene, _ = _scene_with_questions(["Q1"], 4)
    scene._cast_vote(True)
    scene._cast_vote(True)
    scene._cast_vote(False)
    scene._cast_vote(False)
    # 同数の場合のルール: len(yes) < len(no) でないので no_ids が returned
    assert scene._state == MinorityState.REVEAL
    assert scene._unanimous is False
    assert len(scene._losers_this_round) == 2


def test_next_round_advances():
    scene, _ = _scene_with_questions(["Q1", "Q2"], 2)
    # 1 ラウンド目完了
    scene._cast_vote(True)
    scene._cast_vote(False)
    assert scene._state == MinorityState.REVEAL
    # 次へ
    scene._next_round()
    assert scene._round_idx == 1
    assert scene._state == MinorityState.VOTING


def test_done_after_all_rounds():
    scene, _ = _scene_with_questions(["Q1"], 2)
    scene._cast_vote(True)
    scene._cast_vote(False)
    scene._next_round()
    assert scene._state == MinorityState.DONE


def test_falls_back_when_questions_empty():
    scene, _ = _scene_with_questions([], 2)
    # デフォルト質問が入る
    assert len(scene._questions) > 0
    assert scene._state == MinorityState.VOTING
