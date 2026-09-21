# Model routing

Model choice is separate from verification authority.

## Routes

### deterministic-demo
Credential-free reproducible demonstration. Proves pipeline mechanics only.

### openai-compatible
Designed for Ollama, vLLM, or any compatible local server. Default configuration points to a Qwen coder-family model name. JSON artifacts are schema-validated.

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

A real GitHub Actions smoke now exercises the route with Ollama 0.34.2 and Qwen2.5-Coder 1.5B. The captured run recorded 2 model calls, 3,486 input tokens, 1,208 output tokens, about 120.2 s accumulated model latency, zero schema retries/fallbacks, and a fail-closed block with zero source edits. These remain plumbing/integration measurements, not a model-quality benchmark.


## Coding-agent client boundary

`planprobe preflight` is the vendor-neutral integration point. Claude Code, Cursor, Codex, or another coding agent may invoke the same CLI contract before source editing. This repository claims the implemented CLI boundary, not vendor-specific benchmark results.


## Real open-model smoke

The `open-model-smoke` workflow installs Ollama, pulls `qwen2.5-coder:1.5b`, warms the model, runs `planprobe preflight`, validates the machine-readable packet, and uploads the packet plus exact model inventory as workflow artifacts. The workflow fails if the real model route cannot produce a schema-valid preflight packet or if preflight modifies source.
