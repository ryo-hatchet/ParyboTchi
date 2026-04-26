from nomiboy.colors import PLAYER_COLORS, player_color


def test_player_color_returns_distinct_for_first_4():
    cs = [player_color(i) for i in range(4)]
    assert len(set(cs)) == 4


def test_player_color_wraps_around():
    assert player_color(0) == player_color(4)
