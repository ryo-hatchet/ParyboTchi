import random
from nomiboy.games.bomb import BombController


def test_timer_starts_within_range():
    rng = random.Random(0)
    c = BombController(player_count=3, rng=rng, min_sec=10, max_sec=30)
    c.start()
    assert 10.0 <= c.remaining <= 30.0


def test_pass_advances_holder():
    c = BombController(player_count=3)
    c.start()
    assert c.holder == 0
    c.pass_to_next()
    assert c.holder == 1
    c.pass_to_next(); c.pass_to_next(); c.pass_to_next()
    assert c.holder == 1  # 0→1→2→0→1


def test_tick_decreases_remaining():
    c = BombController(player_count=2)
    c.start()
    initial = c.remaining
    c.tick(0.5)
    assert c.remaining == initial - 0.5


def test_explodes_when_remaining_zero():
    c = BombController(player_count=2)
    c.start()
    c._remaining = 0.0
    assert c.exploded is True


def test_holder_at_explosion():
    c = BombController(player_count=2)
    c.start()
    c.pass_to_next()
    c._remaining = 0.0
    assert c.exploded is True
    assert c.holder == 1
