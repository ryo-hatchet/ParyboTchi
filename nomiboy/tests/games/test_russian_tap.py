"""ロシアン飲酒のコントローラ純ロジックテスト。"""
from __future__ import annotations

import random

import pytest

from nomiboy.games.russian_tap import RussianTapController


def test_start_initializes_state():
    c = RussianTapController(player_count=4, rng=random.Random(0))
    c.start()
    assert c.exploded is False
    assert c.safe_cells == set()
    assert c.loser_index is None
    assert 0 <= c.current_player_index < 4


def test_bomb_position_is_random_but_reproducible():
    c1 = RussianTapController(player_count=3, rng=random.Random(42))
    c1.start()
    c2 = RussianTapController(player_count=3, rng=random.Random(42))
    c2.start()
    # 内部の爆弾位置を比較する手段が無いので、全マスをタップして爆発位置で比較
    bomb_pos_1 = _find_bomb(c1)
    bomb_pos_2 = _find_bomb(c2)
    assert bomb_pos_1 == bomb_pos_2


def test_first_player_is_random_but_reproducible():
    c1 = RussianTapController(player_count=4, rng=random.Random(7))
    c1.start()
    c2 = RussianTapController(player_count=4, rng=random.Random(7))
    c2.start()
    assert c1.current_player_index == c2.current_player_index


def test_safe_tap_adds_cell():
    c = RussianTapController(player_count=2, rng=random.Random(0))
    c.start()
    safe_cell = _any_safe_cell(c)
    is_bomb = c.tap(safe_cell)
    assert is_bomb is False
    assert safe_cell in c.safe_cells
    assert c.exploded is False


def test_safe_tap_advances_player():
    c = RussianTapController(player_count=3, rng=random.Random(0))
    c.start()
    before = c.current_player_index
    safe_cell = _any_safe_cell(c)
    c.tap(safe_cell)
    assert c.current_player_index == (before + 1) % 3


def test_bomb_tap_explodes():
    c = RussianTapController(player_count=4, rng=random.Random(0))
    c.start()
    bomb_cell = _find_bomb_without_consuming(c)
    tapper = c.current_player_index
    is_bomb = c.tap(bomb_cell)
    assert is_bomb is True
    assert c.exploded is True
    assert c.loser_index == tapper


def test_double_tap_same_cell_is_noop():
    c = RussianTapController(player_count=2, rng=random.Random(0))
    c.start()
    safe_cell = _any_safe_cell(c)
    c.tap(safe_cell)
    snapshot = (
        c.current_player_index,
        frozenset(c.safe_cells),
        c.exploded,
        c.loser_index,
    )
    result = c.tap(safe_cell)
    assert result is False
    assert (
        c.current_player_index,
        frozenset(c.safe_cells),
        c.exploded,
        c.loser_index,
    ) == snapshot


def test_tap_after_explosion_is_noop():
    c = RussianTapController(player_count=3, rng=random.Random(0))
    c.start()
    bomb_cell = _find_bomb_without_consuming(c)
    c.tap(bomb_cell)
    assert c.exploded is True
    snapshot = (c.current_player_index, frozenset(c.safe_cells), c.loser_index)
    other_cells = [i for i in range(9) if i != bomb_cell]
    result = c.tap(other_cells[0])
    assert result is False
    assert (c.current_player_index, frozenset(c.safe_cells), c.loser_index) == snapshot


@pytest.mark.parametrize("invalid", [-1, 9, 100, -100])
def test_invalid_cell_index_is_noop(invalid):
    c = RussianTapController(player_count=2, rng=random.Random(0))
    c.start()
    snapshot = (
        c.current_player_index,
        frozenset(c.safe_cells),
        c.exploded,
        c.loser_index,
    )
    result = c.tap(invalid)
    assert result is False
    assert (
        c.current_player_index,
        frozenset(c.safe_cells),
        c.exploded,
        c.loser_index,
    ) == snapshot


def test_bomb_position_uniformly_distributed():
    """1000 回 start して各マスへの爆弾配置回数が一様分布の許容範囲内に収まる。"""
    counts = [0] * 9
    for seed in range(1000):
        c = RussianTapController(player_count=2, rng=random.Random(seed))
        c.start()
        counts[_find_bomb(c)] += 1
    # 期待値 1000/9 ≈ 111、±60 を許容（roulette テストと同様の幅広めゆるい検定）
    assert all(50 < n < 175 for n in counts), counts


def test_turn_cycles_through_players():
    """3 人で 3 回セーフタップすると先攻に戻る（先攻が何であっても循環する）。"""
    c = RussianTapController(player_count=3, rng=random.Random(0))
    c.start()
    start_index = c.current_player_index
    bomb_cell = _find_bomb_without_consuming(c)
    safes = [i for i in range(9) if i != bomb_cell]
    seen = [c.current_player_index]
    for cell in safes[:3]:
        c.tap(cell)
        seen.append(c.current_player_index)
    assert seen == [
        start_index,
        (start_index + 1) % 3,
        (start_index + 2) % 3,
        start_index,
    ]
    assert c.exploded is False


# ───────────────── ヘルパ ─────────────────


def _find_bomb(c: RussianTapController) -> int:
    """全マスを順番にタップして爆弾位置を見つける（破壊的）。"""
    for i in range(9):
        if c.tap(i):
            return i
    raise AssertionError("爆弾が見つからなかった")


def _find_bomb_without_consuming(c: RussianTapController) -> int:
    """非破壊的に爆弾位置を見つける（同 seed の別 controller を作って探索）。"""
    # ※ コントローラ内部の爆弾位置を直接公開していないので、
    # 同じ rng 状態を再現できる別個のコントローラで先に探って爆弾位置を割り出す。
    # しかし RNG の状態は start() 後にも継続するため、
    # 「もう一個同じ seed のコントローラを作る」方式は使えない（呼び出し側の rng がブラックボックス）。
    # よってここでは _bomb_cell を読みに行く（テスト専用パス）。
    return c._bomb_cell  # noqa: SLF001 (テスト便宜のための内部参照)


def _any_safe_cell(c: RussianTapController) -> int:
    """爆弾以外の任意のマス番号を返す。"""
    bomb = c._bomb_cell  # noqa: SLF001
    for i in range(9):
        if i != bomb and i not in c.safe_cells:
            return i
    raise AssertionError("セーフマスが残っていない")
