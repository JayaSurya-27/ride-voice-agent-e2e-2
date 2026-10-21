from __future__ import annotations

import os

from livekit.plugins import deepgram


def build_deepgram_stt(api_key: str, model: str):
    """Flux uses Deepgram's v2 API; Nova models use the v1 API."""
    if model.startswith("flux-"):
        return deepgram.STTv2(api_key=api_key, model=model)
    return deepgram.STT(api_key=api_key, model=model)


def google_llm_kwargs() -> dict:
    """The LLM runs on the Gemini API with an API key (no Vertex)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY for the Gemini API.")
    return {"vertexai": False, "api_key": api_key}
