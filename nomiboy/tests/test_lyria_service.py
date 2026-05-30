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


def test_generate_calls_genai_and_returns_bytes():
    fake_audio = b"FAKE_WAV_BYTES"
    fake_part = MagicMock()
    fake_part.inline_data.data = fake_audio
    fake_response = MagicMock()
    fake_response.candidates = [MagicMock()]
    fake_response.candidates[0].content.parts = [fake_part]

    with patch("nomiboy.core.lyria_service.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = fake_response
        mock_genai.Client.return_value = mock_client

        svc = LyriaService(api_key="dummy-key")
        result = svc.synthesize_call("たろう", _tmpl())

    assert result == fake_audio
    mock_genai.Client.assert_called_once()
    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "lyria-3-pro-preview"
    # プロンプトに名前が含まれている
    contents_arg = call_kwargs["contents"]
    text_payload = str(contents_arg)
    assert "たろう" in text_payload
    assert "upbeat chant" in text_payload


def test_generate_returns_none_on_exception():
    with patch("nomiboy.core.lyria_service.genai") as mock_genai:
        mock_genai.Client.side_effect = RuntimeError("boom")
        svc = LyriaService(api_key="dummy-key")
        assert svc.synthesize_call("たろう", _tmpl()) is None


def test_generate_returns_none_when_no_audio_part():
    with patch("nomiboy.core.lyria_service.genai") as mock_genai:
        mock_client = MagicMock()
        empty_response = MagicMock()
        empty_response.candidates = []
        mock_client.models.generate_content.return_value = empty_response
        mock_genai.Client.return_value = mock_client

        svc = LyriaService(api_key="dummy-key")
        assert svc.synthesize_call("たろう", _tmpl()) is None
