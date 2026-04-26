import pytest
from nomiboy.stores.player_store import PlayerStore, Player


def test_store_starts_empty():
    s = PlayerStore()
    assert s.players == []
    assert s.count == 0


def test_add_assigns_sequential_id():
    s = PlayerStore()
    s.add("たろう"); s.add("はなこ")
    assert [p.id for p in s.players] == [0, 1]


def test_add_assigns_color_from_palette():
    s = PlayerStore()
    s.add("a"); s.add("b")
    assert s.players[0].color != s.players[1].color


def test_max_4_players():
    s = PlayerStore()
    for n in "abcd":
        s.add(n)
    with pytest.raises(ValueError):
        s.add("e")


def test_can_start_requires_min_2():
    s = PlayerStore()
    s.add("a")
    assert not s.can_start()
    s.add("b")
    assert s.can_start()


def test_remove_by_index():
    s = PlayerStore()
    s.add("a"); s.add("b"); s.add("c")
    s.remove(1)
    assert [p.name for p in s.players] == ["a", "c"]


def test_clear():
    s = PlayerStore()
    s.add("a"); s.add("b")
    s.clear()
    assert s.players == []


def test_name_max_length_8():
    s = PlayerStore()
    with pytest.raises(ValueError):
        s.add("123456789")  # 9文字
