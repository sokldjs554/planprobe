from __future__ import annotations

from planprobe.agent.factory import build_provider
from planprobe.agent.ollama_native import OllamaProvider
from planprobe.agent.openai_compat import OpenAICompatibleProvider


def test_provider_factory_separates_native_ollama_from_openai_compat() -> None:
    assert isinstance(build_provider("ollama"), OllamaProvider)
    assert isinstance(build_provider("openai-compatible"), OpenAICompatibleProvider)
    assert isinstance(build_provider("vllm"), OpenAICompatibleProvider)
