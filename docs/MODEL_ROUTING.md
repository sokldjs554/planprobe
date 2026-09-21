# Model routing

Model choice is separate from verification authority.

## Routes

### deterministic-demo
Credential-free reproducible demonstration. Proves pipeline mechanics only.

### openai-compatible
Used for Ollama, vLLM, or another OpenAI-compatible local/server endpoint. JSON artifacts are schema-validated. The verified real open-model smoke uses Ollama's OpenAI-compatible endpoint with Qwen2.5-Coder 1.5B.

### anthropic
Optional hosted route for planning/replanning/patch proposals.

## Authority boundary

No model route can:
- return the final assumption verdict;
- execute arbitrary shell commands;
- edit tests, probe runtime, gate rules, or CI;
- choose to skip a load-bearing probe;
- downgrade `contradicted`/`unknown` into `verified`.

Those decisions live in deterministic Python code.

## Repository context transport

Remote/local model adapters receive a bounded source pack rather than a local filesystem path they cannot access. The demo prefers `synthetic_app/liveops_service`; external preflight workspaces fall back to the selected workspace, excluding generated/vendor directories such as `.git`, virtual environments, caches, build outputs, and `node_modules`. `PLANPROBE_CONTEXT_ROOTS` can explicitly narrow the packed roots. Repository contents remain untrusted data and the pack is size-bounded.

## Usage evidence

When the provider API returns usage data, PlanProbe records model route, model id, call count, input/output tokens, and accumulated model latency in the run packet. `scripts/run_model_smoke.py` writes an auditable smoke artifact without storing API keys.

The real GitHub Actions smoke exercises the OpenAI-compatible route against Ollama with Qwen2.5-Coder 1.5B. Run-specific call counts, tokens, latency, schema retries/fallbacks, and rejected probe candidates are kept in the workflow packet/artifact rather than frozen into this document. The smoke requires zero source edits, no probe-runtime failure, and at least one decisive repository probe with evidence. Invalid model-proposed probe candidates are rejected before execution; missing load-bearing evidence remains fail-closed. These remain integration/verification-boundary measurements, not a model-quality benchmark.


## Coding-agent client boundary

`planprobe preflight` is the vendor-neutral integration point. Claude Code, Cursor, Codex, or another coding agent may invoke the same CLI contract before source editing. This repository claims the implemented CLI boundary, not vendor-specific benchmark results.


## Real open-model smoke

The `open-model-smoke` workflow installs Ollama, pulls `qwen2.5-coder:1.5b`, warms the model, runs `planprobe preflight`, validates the machine-readable packet, and uploads the packet plus exact model inventory as workflow artifacts. It fails when there is no decisive executable repository probe with evidence, when a probe reaches runtime in an invalid form, when the model route cannot produce the packet, or when preflight modifies source.
