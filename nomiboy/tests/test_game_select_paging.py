"""GameSelectScene のページング機構テスト。"""
from __future__ import annotations

import pygame
import pytest

from nomiboy.games import GameMeta
from nomiboy.scenes.game_select import GameSelectScene


pygame.init()


class StubAssets:
    def font(self, name: str, size: int):
        return pygame.font.Font(None, size)


class StubAppContext:
    def __init__(self) -> None:
        self.assets = StubAssets()
        self.players = None
        self.online = False


class StubSceneManager:
    def __init__(self) -> None:
        self.pushed: list = []

    def push(self, scene) -> None:
        self.pushed.append(scene)

    def pop(self) -> None:
        pass

    def reset_to(self, scene) -> None:
        pass


def _make_meta(n: int) -> list[GameMeta]:
    return [
        GameMeta(
            key=f"g{i}",
            title=f"G{i}",
            icon=None,
            min_players=2,
            max_players=4,
        )
        for i in range(n)
    ]


@pytest.fixture
def make_scene(monkeypatch):
    def _factory(meta_count: int) -> GameSelectScene:
        monkeypatch.setattr(
            "nomiboy.scenes.game_select.GAME_META", _make_meta(meta_count)
        )
        scene = GameSelectScene(StubSceneManager())
        scene.on_enter(StubAppContext())
        return scene

    return _factory


def test_no_paging_when_4_or_fewer_games(make_scene):
    scene = make_scene(4)
    assert scene.total_pages == 1
    assert scene.nav_buttons == []
    assert len(scene.game_buttons) == 4


def test_paging_shown_when_5_or_more(make_scene):
    scene = make_scene(5)
    assert scene.total_pages == 2
    assert len(scene.nav_buttons) == 2
    assert len(scene.game_buttons) == 4  # 1ページ目には4個


def test_next_page_advances(make_scene):
    scene = make_scene(5)
    assert scene.current_page == 0
    scene.nav_buttons[1].on_tap()
    assert scene.current_page == 1
    assert len(scene.game_buttons) == 1  # 5 − 4 = 1個


def test_prev_page_disabled_on_first(make_scene):
    scene = make_scene(5)
    assert scene.nav_buttons[0].enabled is False
    assert scene.nav_buttons[1].enabled is True


def test_next_page_disabled_on_last(make_scene):
    scene = make_scene(5)
    scene.nav_buttons[1].on_tap()  # 最終ページへ
    assert scene.current_page == 1
    assert scene.nav_buttons[0].enabled is True
    assert scene.nav_buttons[1].enabled is False


def test_page_indicator_count_matches_pages(make_scene):
    scene = make_scene(9)  # ceil(9 / 4) = 3 ページ
    assert scene.total_pages == 3
