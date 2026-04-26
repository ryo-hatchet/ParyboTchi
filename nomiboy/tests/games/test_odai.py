import json
import random
from nomiboy.games.odai import OdaiController, OdaiCard


def make_cards(n=10):
    return [OdaiCard(id=str(i), text=f"text{i}") for i in range(n)]


def test_pick_returns_card():
    rng = random.Random(0)
    c = OdaiController(cards=make_cards(5), rng=rng)
    card = c.next_card()
    assert card.text.startswith("text")


def test_recent_n_excluded():
    rng = random.Random(0)
    cards = make_cards(5)
    c = OdaiController(cards=cards, rng=rng, recent_window=3)
    seen = []
    for _ in range(8):
        seen.append(c.next_card().id)
    for i in range(len(seen) - 2):
        assert len(set(seen[i:i + 3])) == 3


def test_load_from_json(tmp_path):
    path = tmp_path / "o.json"
    path.write_text(json.dumps([{"id": "1", "text": "a"}]), encoding="utf-8")
    cards = OdaiController.load_cards(path)
    assert cards == [OdaiCard(id="1", text="a")]


def test_load_falls_back_when_missing(tmp_path):
    cards = OdaiController.load_cards(tmp_path / "missing.json")
    assert len(cards) >= 5
