# Coding-agent integration

PlanProbe is not tied to Claude Code. The integration boundary is a process-level **preflight contract** that any coding agent capable of running a CLI command can call before editing source files.

## Contract

```bash
planprobe preflight \
  --workspace . \
  --provider openai-compatible \
  --request "Add the requested feature without breaking existing repository contracts." \
  --output .planprobe/preflight.json
```

Exit codes:

- `0`: every load-bearing premise was verified by allowlisted repository probes.
- `2`: at least one load-bearing premise was contradicted or could not be verified. The coding agent must not write source code yet.
- other non-zero: execution/configuration failure.

The JSON output contains the tentative plan, assumptions, executable probe specs, repository evidence, deterministic verdicts, and the gate decision. Preflight itself does **not** create or apply a patch.

## Agent clients

The same contract can be invoked from Claude Code, Cursor, Codex CLI/ChatGPT coding workflows, CI, or another coding agent. The repository does not claim that each vendor client has been independently benchmarked; the implemented artifact is the vendor-neutral CLI boundary.

### OpenAI-compatible local/open route

```bash
export PLANPROBE_OPENAI_BASE_URL=http://127.0.0.1:11434/v1
export PLANPROBE_OPENAI_MODEL=qwen2.5-coder:7b
planprobe preflight --workspace . --provider openai-compatible --request "..."
```

### Hosted Messages route

```bash
export ANTHROPIC_API_KEY=...
planprobe preflight --workspace . --provider anthropic --request "..."
```

## Safety boundary

The model may propose a plan and allowlisted probe definitions, but it cannot mark its own premise as verified. Probe execution and gate policy remain deterministic, and preflight returns `source_edits=0`.
