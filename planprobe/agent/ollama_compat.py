from __future__ import annotations

import os

from planprobe.agent.openai_compat import OpenAICompatibleProvider


class OllamaProvider(OpenAICompatibleProvider):
    name = "ollama"

    def __init__(self) -> None:
        super().__init__()
        base = os.getenv("PLANPROBE_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        self.base_url = f"{base}/v1"
        self.model = os.getenv("PLANPROBE_OLLAMA_MODEL", "qwen2.5-coder:1.5b")
