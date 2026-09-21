# GameSpring AI Programmer JD traceability

Target checked again on 2026-09-21 against the currently open posting (`rec_idx=55022932`, 2026-09-14 → 2026-11-13) and the detailed preceding same-role posting.

| Posting requirement | PlanProbe evidence | Gate |
|---|---|---|
| LLM-based development/work productivity service | prevents wasted coding loops caused by false repository premises | core product |
| Full-stack web application | FastAPI API + Korean product console | implemented |
| LLM API integration | hosted Messages adapter | implemented; real run not yet claimed |
| Open-source model integration | OpenAI-compatible Ollama/vLLM/Qwen route | implemented; benchmark pending |
| Fast prototyping | one request drives plan → probes → replan → patch → tests | implemented |
| AI agent / automation pipeline | multi-stage bounded agent workflow | implemented |
| Code generation | verified plan emits exact source patch | implemented |
| Claude Code / Cursor capability | CLAUDE.md, AGENTS.md, Cursor rules; pre-code gate concept plugs into coding-agent workflow | implemented repo integration |
| Frontend + backend breadth | browser product UI + API/store/worker/pipeline | implemented |
| Solo planning-to-deployment | local implementation and CI manifest now; GitHub/Render deployment still pending | pending final gate |
| Current English AI documentation/trends | collision audit references contemporary agent verification work | documented |

## Current gap list

- Real local/open-source model run has not been measured.
- Hosted model run has not been measured.
- Public GitHub repository, CI result, Render deployment, and deployed E2E do not exist yet.
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
