"""LyriaService 単体テスト。"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from nomiboy.core.lyria_service import CallTemplate, LyriaService


def _tmpl() -> CallTemplate:
    return CallTemplate(
        style="upbeat chant",
        lyrics_template="Lyrics:\n[Chorus]\n{name} が飲んで！",
        duration_sec=10,
    )


def test_synthesize_returns_none_when_api_key_missing():
    svc = LyriaService(api_key=None)
    assert svc.synthesize_call("たろう", _tmpl()) is None


def test_synthesize_returns_none_when_disabled():
    svc = LyriaService(api_key="dummy", disabled=True)
    assert svc.synthesize_call("たろう", _tmpl()) is None


def test_calltemplate_substitutes_name():
    t = _tmpl()
    assert "{name}" in t.lyrics_template
    assert "たろう" in t.lyrics_template.replace("{name}", "たろう")
