import random
from nomiboy.games.roulette import RouletteController


def test_initial_state_spinning():
    c = RouletteController(player_count=3)
    c.start()
    assert c.is_spinning is True


def test_stop_picks_one():
    rng = random.Random(0)
    c = RouletteController(player_count=4, rng=rng)
    c.start()
    c.stop()
    assert c.is_spinning is False
    assert 0 <= c.selected_index < 4


def test_pick_is_uniform_enough():
    rng = random.Random(0)
    counts = [0, 0, 0, 0]
    for _ in range(1000):
        c = RouletteController(player_count=4, rng=rng)
        c.start(); c.stop()
        counts[c.selected_index] += 1
    assert all(150 < c < 350 for c in counts)
