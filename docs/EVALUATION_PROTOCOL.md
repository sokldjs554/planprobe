# Evaluation protocol

## Research question

Does executable pre-code premise falsification reduce repository-invalid implementation attempts compared with common coding-agent workflows?

The evaluation is split into two layers so deterministic verification mechanics are not confused with model quality.

## Phase A — frozen repository-contract suite (implemented)

Purpose: test the probe DSL and source-write gate against repository facts whose truth is fixed in advance.

The v1 suite contains **24 cases across 6 premise classes**, four cases per class:

- schema cardinality/type;
- timezone/config policy;
- idempotency/retry;
- call/order/state transition;
- backward compatibility;
- authorization/ownership.

Each case freezes:

1. a tiny repository state;
2. one load-bearing premise;
3. one allowlisted executable probe;
4. the expected tri-state verdict (`verified`, `contradicted`, `unknown`);
5. the expected source-write gate (`pass`, `block`).

The suite also hashes Python source before and after every probe. A probe may create interpreter/test cache files, but must not modify source.

Run:

```bash
PYTHONPATH=. python scripts/evaluate_probe_suite.py
```

Current local result (`artifacts/probe-suite.json`):

- verdict classification: **24/24 correct**;
- gate decision: **24/24 correct**;
- source unchanged during probing: **24/24**;
- false blocks: **0**;
- missed blocks: **0**;
- explicit `unknown`/abstain cases: **6**;
- median probe latency: ~**0.1 ms** for the mixed suite; pytest-backed probes dominate tail latency;
- p95 probe latency: ~**1.7 s** in the current container.

These numbers measure the deterministic repository-probe mechanics only. They are **not** evidence that an LLM discovers assumptions correctly.

## Phase B — model comparison (protocol frozen, execution pending)

Conditions:

1. **Direct** — request → code.
2. **Self-reflect** — request → plan/self-review → code.
3. **PlanProbe** — request → plan → premise extraction → executable probes → gate/replan → code.

Use at least 24 synthetic-but-realistic repository tasks spanning the same six premise classes. Conditions receive the same request, repository state, immutable acceptance checks, model family, and generation budget.

### Metrics

- task success;
- invalid-premise patch rate;
- number of source edits before first repository contradiction is discovered;
- first-attempt acceptance;
- false-block rate;
- unresolved/unknown rate;
- latency p50/p95;
- input/output tokens and model-call count;
- patch size;
- repair iterations.

### Model routes

After the deterministic harness is stable:

- local/open model through Ollama/vLLM (Qwen coder-family route);
- hosted model through API.

The adapters now send a bounded repository source pack instead of a meaningless local filesystem path, and record call/token/latency metadata when the provider returns usage data.

`python scripts/run_model_smoke.py --provider ...` persists one auditable smoke artifact. Do not publish model-quality numbers until raw run artifacts and exact model identifiers/revisions exist.
