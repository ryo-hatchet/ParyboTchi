"""nomiboy ゲーム一覧。GameSelectScene が参照する。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GameMeta:
    key: str
    title: str
    icon: str | None
    min_players: int
    max_players: int


GAME_META: list[GameMeta] = [
    GameMeta(key="bomb", title="BOMB", icon="bomb.png", min_players=2, max_players=4),
    GameMeta(key="roulette", title="ROULETTE", icon="roulette.png", min_players=2, max_players=4),
    GameMeta(key="odai", title="ODAI", icon="odai.png", min_players=2, max_players=4),
    GameMeta(key="russian_tap", title="ロシアン飲酒", icon=None, min_players=2, max_players=8),
]
