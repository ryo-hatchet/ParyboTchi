"""CallPlayer 単体テスト。"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from nomiboy.core.call_player import CallPlayer, load_call_templates
from nomiboy.core.lyria_service import CallTemplate
from nomiboy.stores.player_store import Player


def _player(pid: int = 1, name: str = "たろう") -> Player:
    return Player(id=pid, name=name, color=(255, 0, 0))


def _templates() -> list[CallTemplate]:
    return [
        CallTemplate(style="s1", lyrics_template="Lyrics:\n{name}", duration_sec=10),
    ]


def test_load_call_templates_from_json(tmp_path: Path):
    payload = [
        {"style": "s", "lyrics_template": "Lyrics:\n{name}", "duration_sec": 10},
    ]
    p = tmp_path / "call_prompts.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    templates = load_call_templates(p)
    assert len(templates) == 1
    assert templates[0].style == "s"


def test_load_call_templates_returns_default_when_missing(tmp_path: Path):
    p = tmp_path / "missing.json"
    templates = load_call_templates(p)
    assert len(templates) >= 1
    assert "{name}" in templates[0].lyrics_template


def test_play_returns_false_when_no_future():
    lyria = MagicMock()
    audio = MagicMock()
    cp = CallPlayer(lyria=lyria, audio=audio, templates=_templates())
    assert cp.play(_player()) is False


def test_prefetch_calls_lyria_for_each_player(monkeypatch):
    lyria = MagicMock()
    lyria.synthesize_call.return_value = b"FAKEWAV"
    audio = MagicMock()

    fake_sound = MagicMock()
    monkeypatch.setattr("nomiboy.core.call_player.pygame.mixer.Sound", lambda _bio: fake_sound)

    cp = CallPlayer(lyria=lyria, audio=audio, templates=_templates(), max_workers=2, play_wait_sec=2.0)
    players = [_player(1, "たろう"), _player(2, "はなこ")]
    cp.prefetch(players)

    assert cp.play(players[0]) is True
    assert cp.play(players[1]) is True
    fake_sound.play.assert_called()
    assert lyria.synthesize_call.call_count == 2
    cp.clear()


def test_prefetch_with_failed_generation_returns_false(monkeypatch):
    lyria = MagicMock()
    lyria.synthesize_call.return_value = None  # 失敗
    audio = MagicMock()

    cp = CallPlayer(lyria=lyria, audio=audio, templates=_templates(), max_workers=1, play_wait_sec=1.0)
    p = _player(1, "たろう")
    cp.prefetch([p])

    assert cp.play(p) is False
    cp.clear()


def test_prefetch_empty_list_is_noop():
    lyria = MagicMock()
    cp = CallPlayer(lyria=lyria, audio=MagicMock(), templates=_templates())
    cp.prefetch([])
    assert cp.play(_player()) is False


def test_clear_resets_state(monkeypatch):
    lyria = MagicMock()
    lyria.synthesize_call.return_value = b"FAKE"
    monkeypatch.setattr("nomiboy.core.call_player.pygame.mixer.Sound", lambda _bio: MagicMock())

    cp = CallPlayer(lyria=lyria, audio=MagicMock(), templates=_templates())
    cp.prefetch([_player(1)])
    cp.clear()
    assert cp.play(_player(1)) is False
