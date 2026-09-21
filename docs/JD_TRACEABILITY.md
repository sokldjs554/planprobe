# GameSpring AI Programmer JD traceability

Target checked again on 2026-09-21 against the currently open posting (`rec_idx=55022932`, 2026-09-14 → 2026-11-13) and the detailed preceding same-role posting.

| Posting requirement | PlanProbe evidence | Gate |
|---|---|---|
| LLM-based development/work productivity service | prevents wasted coding loops caused by false repository premises | core product |
| Full-stack web application | FastAPI API + Korean product console | implemented |
| LLM API integration | hosted Messages adapter | implemented; real run not yet claimed |
| Open-source model integration | OpenAI-compatible route + actual Ollama/Qwen2.5-Coder 1.5B smoke artifact | implemented and smoke-verified |
| Fast prototyping | one request drives plan → probes → replan → patch → tests | implemented |
| AI agent / automation pipeline | multi-stage bounded agent workflow | implemented |
| Code generation | verified plan emits exact source patch | implemented |
| Claude Code / Cursor capability | CLAUDE.md, AGENTS.md, Cursor rules; pre-code gate concept plugs into coding-agent workflow | implemented repo integration |
| Frontend + backend breadth | browser product UI + API/store/worker/pipeline | implemented |
| Solo planning-to-deployment | public GitHub + Python 3.11/3.12/3.13 CI + Render + exact-commit deployed E2E | implemented and verified |
| Current English AI documentation/trends | collision audit references contemporary agent verification work | documented |

## Current gap list

- Real local/open-source **smoke integration has been measured**; model-quality comparison is still pending.
- Hosted model run has not been measured.
- Comparative evaluation vs direct coding / self-reflect is designed but not yet executed.

No application document should claim these pending items as completed.

## Gate 2 — frozen probe-suite expansion (2026-09-21)

The posting requirements were rechecked before expanding the research surface. No feature was added solely for benchmark aesthetics; the expansion strengthens the same role-relevant product story:

- development productivity: prevent invalid coding loops before source modification;
- LLM API/open-model readiness: provider routes now receive bounded repository contents and expose usage metrics;
- AI pipeline: plan → implicit premise → executable probe → deterministic gate → evidence-bound replan → code → verification;
- full-stack proof: the Korean product console remains the reviewer-facing surface while the probe suite and model-smoke artifacts provide deeper engineering evidence;
- rapid proof: CI can execute the 24-case repository-contract suite without model credentials.

Measured deterministic contract-suite evidence now exists for six repository premise classes (schema, timezone/config, retry/idempotency, state order, backward compatibility, authorization/ownership). This is verification-engine evidence only; Direct/Self-reflect/real-model comparative claims remain pending.


## Gate 3 — GitHub CI + public deployment (2026-09-21)

The currently open GameSpring posting (`rec_idx=55022932`, 2026-09-14 → 2026-11-13) was rechecked before closing this gate. The preceding detailed same-role posting still maps directly to the implemented system: LLM-based development/work productivity tooling, full-stack web delivery with LLM API/open-model integration, AI-agent/code-generation automation, Claude Code/Cursor-style development, and fast evidence of a solo full-stack build.

Verified implementation evidence:
- public repository: `sokldjs554/planprobe`;
- Korean full-stack product console + FastAPI backend;
- CI on Python 3.11/3.12/3.13: dependency check, pytest, Ruff, mypy, TypeScript strict typecheck, 24-case repository-contract suite, deterministic end-to-end gate;
- public Render service: `https://planprobe.onrender.com`;
- independent deployed E2E waits until `/api/release` equals the exact `github.sha` under test, then submits the public demo request and verifies pre-code blocking and final `ready_with_evidence` output;
- the CI process found real lint/type defects during publication; the implementation was fixed rather than weakening the gates.

Still deliberately unclaimed:
- real Qwen/Ollama/vLLM model-quality benchmark;
- hosted-model quality benchmark;
- comparative superiority over Direct coding / Self-reflect.

These remaining research experiments are not required to claim that the product, CI, deployment, and deterministic verification engine exist and are operational.


## Gate 4 — vendor-neutral coding-agent preflight (2026-09-21)

A product-fit check was run before this expansion. The change strengthens the posting's Vibe Coding / AI-tool usage requirement without making PlanProbe Claude-only.

Implemented:
- `planprobe preflight --workspace ... --provider ... --request ...`;
- process exit code 0 for verified preflight and 2 for a blocked pre-code gate;
- machine-readable JSON evidence packet;
- zero source modifications during preflight;
- repository context fallback for non-demo workspaces, with bounded file types and excluded generated/vendor directories;
- documented compatibility boundary for Claude Code, Cursor, Codex, and other coding agents that can invoke a CLI command.

Collision check at this gate searched public GitHub for combinations of coding-agent preflight, repository assumptions, executable premise probes, and source-write interlocks. No directly matching repository was found in those searches. This is not a claim of global novelty.

Still unclaimed:
- vendor-specific benchmark quality;
- real Qwen/hosted model comparative results;
- superiority over direct coding/self-reflect baselines.


## Gate 5 — real open-model smoke (2026-09-21)

The open-model verification path runs **Ollama + Qwen2.5-Coder 1.5B** in GitHub Actions through the OpenAI-compatible adapter.

Current acceptance contract:
- the runner installs Ollama, pulls the exact model tag, records model inventory, and warms the model;
- `planprobe preflight` must leave source modifications at **0**;
- model-proposed probe candidates are semantically validated before execution;
- invalid candidates are rejected rather than executed, and missing load-bearing evidence remains fail-closed;
- at least one real repository probe must reach a decisive `verified` or `contradicted` verdict with repository evidence;
- probe-runtime failures make the smoke fail;
- the preflight packet and exact model inventory are retained as Actions artifacts.

Run-specific token/latency/rejection counts are evidence attached to the workflow run, not fixed portfolio performance claims. This closes the "open-source model route exists only on paper" gap only when the current smoke is green. It does **not** establish model-quality superiority, and hosted-model / Direct-vs-Self-reflect comparisons remain deliberately unclaimed.
