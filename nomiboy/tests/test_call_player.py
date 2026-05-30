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
