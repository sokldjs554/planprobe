from __future__ import annotations

from planprobe.agent.factory import build_provider
from planprobe.agent.ollama_compat import OllamaProvider
from planprobe.agent.openai_compat import OpenAICompatibleProvider


def test_provider_factory_routes_ollama_through_compatibility_adapter() -> None:
    assert isinstance(build_provider("ollama"), OllamaProvider)
    assert isinstance(build_provider("openai-compatible"), OpenAICompatibleProvider)
    assert isinstance(build_provider("vllm"), OpenAICompatibleProvider)
