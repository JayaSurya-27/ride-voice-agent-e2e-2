import pytest
from livekit.plugins import deepgram
from uber_voice_agent.config import build_deepgram_stt, google_llm_kwargs


def test_flux_uses_deepgram_v2() -> None:
    assert isinstance(build_deepgram_stt("test-key", "flux-general-en"), deepgram.STTv2)


def test_phone_nova_uses_deepgram_v1() -> None:
    assert isinstance(build_deepgram_stt("test-key", "nova-2-phonecall"), deepgram.STT)


def test_llm_uses_gemini_api_key_only(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    assert google_llm_kwargs() == {"vertexai": False, "api_key": "test-key"}


def test_llm_requires_gemini_api_key(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        google_llm_kwargs()
