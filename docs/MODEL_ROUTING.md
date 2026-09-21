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

Remote/local model adapters receive a bounded deterministic source pack from `synthetic_app/liveops_service` rather than a local filesystem path they cannot access. Repository contents are marked as untrusted data. The context pack is size-bounded and does not expand arbitrary paths.

## Usage evidence

When the provider API returns usage data, PlanProbe records model route, model id, call count, input/output tokens, and accumulated model latency in the run packet. `scripts/run_model_smoke.py` writes an auditable smoke artifact without storing API keys.

These metrics are plumbing evidence only until a frozen comparative model run is executed.
