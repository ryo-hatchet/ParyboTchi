"""LyricsService 単体テスト。"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from nomiboy.core.lyrics_service import LyricsService, _default_lyrics


def test_returns_none_when_api_key_missing():
    svc = LyricsService(api_key=None)
    result = svc.generate_song_lyrics("ヘビーメタル", {"たろう": 0.9})
    assert result is None


def test_returns_none_when_emphasis_empty():
    svc = LyricsService(api_key="dummy")
    result = svc.generate_song_lyrics("J-POP", {})
    assert result is None


def test_default_lyrics_includes_genre_and_names():
    text = _default_lyrics("ロック", ["たろう", "はなこ"])
    assert "ロック" in text
    assert "たろう" in text
    assert "はなこ" in text
    assert "[Chorus]" in text
    assert "乾杯" in text


def test_generate_calls_gemini_and_returns_text():
    fake_text = "Lyrics:\n[Intro]\nどんちゃん騒ぎ\n[Chorus]\n乾杯！"
    fake_part = MagicMock()
    fake_part.text = fake_text
    fake_response = MagicMock()
    fake_response.candidates = [MagicMock()]
    fake_response.candidates[0].content.parts = [fake_part]

    with patch("nomiboy.core.lyrics_service.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = fake_response
        mock_genai.Client.return_value = mock_client

        svc = LyricsService(api_key="dummy")
        result = svc.generate_song_lyrics("EDM", {"たろう": 0.8, "はなこ": 0.3})

    assert result == fake_text
    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-3.5-flash"
    prompt = str(call_kwargs["contents"])
    assert "EDM" in prompt
    assert "たろう" in prompt
    assert "0.8" in prompt


def test_generate_returns_none_on_exception():
    with patch("nomiboy.core.lyrics_service.genai") as mock_genai:
        mock_genai.Client.side_effect = RuntimeError("boom")
        svc = LyricsService(api_key="dummy")
        result = svc.generate_song_lyrics("ロック", {"たろう": 0.5})
        assert result is None


def test_generate_returns_none_when_no_candidates():
    with patch("nomiboy.core.lyrics_service.genai") as mock_genai:
        mock_client = MagicMock()
        empty = MagicMock()
        empty.candidates = []
        mock_client.models.generate_content.return_value = empty
        mock_genai.Client.return_value = mock_client

        svc = LyricsService(api_key="dummy")
        result = svc.generate_song_lyrics("J-POP", {"たろう": 0.5})
        assert result is None
