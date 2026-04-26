"""プレイヤー登録ストア。"""
from __future__ import annotations

from dataclasses import dataclass

from nomiboy.colors import player_color

MAX_PLAYERS = 4
MIN_PLAYERS_TO_START = 2
MAX_NAME_LEN = 8


@dataclass(frozen=True)
class Player:
    id: int
    name: str
    color: tuple[int, int, int]


class PlayerStore:
    def __init__(self) -> None:
        self._players: list[Player] = []
        self._next_id: int = 0

    @property
    def players(self) -> list[Player]:
        return list(self._players)

    @property
    def count(self) -> int:
        return len(self._players)

    def add(self, name: str) -> Player:
        if len(name) == 0 or len(name) > MAX_NAME_LEN:
            raise ValueError(f"name length must be 1-{MAX_NAME_LEN}")
        if len(self._players) >= MAX_PLAYERS:
            raise ValueError(f"max {MAX_PLAYERS} players")
        p = Player(id=self._next_id, name=name, color=player_color(len(self._players)))
        self._players.append(p)
        self._next_id += 1
        return p

    def remove(self, index: int) -> None:
        del self._players[index]

    def clear(self) -> None:
        self._players.clear()
        self._next_id = 0

    def can_start(self) -> bool:
        return len(self._players) >= MIN_PLAYERS_TO_START
