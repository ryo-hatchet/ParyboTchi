import pytest
from pathlib import Path
from nomiboy.core.tts_service import TTSService


def test_speak_returns_cached_path_when_exists(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    text = "こんにちは"
    svc = TTSService(api_key=None, cache_dir=cache)
    key = svc.cache_key(text, voice="default")
    expected_path = cache / f"{key}.wav"
    expected_path.write_bytes(b"FAKE")
    assert svc.speak(text) == expected_path


def test_speak_returns_none_when_offline_and_no_cache(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    svc = TTSService(api_key=None, cache_dir=cache)
    assert svc.speak("uncached text") is None


def test_speak_swallows_exceptions(tmp_path, monkeypatch):
    cache = tmp_path / "cache"; cache.mkdir()
    svc = TTSService(api_key="dummy", cache_dir=cache)
    def boom(*a, **kw):
        raise RuntimeError("boom")
    monkeypatch.setattr(svc, "_synthesize", boom)
    assert svc.speak("anything") is None
