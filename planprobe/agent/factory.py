from __future__ import annotations

from planprobe.agent.anthropic import AnthropicProvider
from planprobe.agent.base import AgentProvider
from planprobe.agent.deterministic import DeterministicDemoProvider
from planprobe.agent.ollama_native import OllamaProvider
from planprobe.agent.openai_compat import OpenAICompatibleProvider


def build_provider(name: str) -> AgentProvider:
    if name == "deterministic-demo":
        return DeterministicDemoProvider()
    if name == "ollama":
        return OllamaProvider()
    if name in {"openai-compatible", "vllm"}:
        return OpenAICompatibleProvider()
    if name == "anthropic":
        return AnthropicProvider()
    raise ValueError(f"Unsupported provider: {name}")
