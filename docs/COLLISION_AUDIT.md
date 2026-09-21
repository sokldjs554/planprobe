# Collision audit

Research checkpoint: 2026-09-21

The topic was re-audited immediately before implementation because the application strategy explicitly prioritizes low portfolio-topic collision.

## Directly adjacent public work discovered

### Teycir/Assumptions
Turns an existing code diff into an evidence-backed assumption ledger, including failure modes and suggested falsification tests.

**Collision risk:** high if PlanProbe were only an assumption list/reviewer.

**PlanProbe boundary:** pre-code rather than post-diff; assumptions are extracted from a tentative implementation plan; tests are compiled into an allowlisted executable probe DSL and actually run; load-bearing failure blocks source edits; evidence feeds an automatic replan and only then a patch is permitted.

### pirate/codex-structured-steering
Surfaces implicit coding-agent decisions/assumptions for a human to correct via UI controls.

**Collision risk:** high if the project merely surfaced assumptions.

**PlanProbe boundary:** repository evidence, not human toggles, resolves the main gate; `verified` cannot be emitted by the planning model.

### adelattef/captains-box
Build-plan interlock that requires assumptions/citations to be present and evidence references to be valid before a plan authorizes a build.

**Collision risk:** meaningful.

**PlanProbe boundary:** automatic implicit-premise extraction + executable repository probes + tri-state verdict + evidence-bound replanning + generated patch + post-patch verification. The core artifact is a machine-executed pre-code falsification run, not a plan-document grammar.

### 263311487-ux/falsify
General falsification reasoning protocol for agents.

**Collision risk:** low to medium.

**PlanProbe boundary:** concrete developer product, repo-specific evidence, finite probe runtime, hard source-write gate, full-stack UI, patch lifecycle.

## Rejected interpretations

- assumption checklist;
- chat-based "ask your repo" tool;
- generic code reviewer;
- prompt-only Claude/Cursor skill;
- human toggle board for agent decisions;
- plan document linter.

## Novelty axis retained

**Plan → implicit premise → executable probe → deterministic verdict → source-write interlock → evidence-bound replan → code**.

This does not claim global novelty. It is the narrower product boundary chosen after collision auditing.

## Gate 2 re-audit after probe-suite design

Additional GitHub searches were run around `pre-code assumption probe`, `repository premise probe compiler`, `coding agent source write gate assumptions`, and `implementation plan assumption verification agent`.

No directly matching public repository was found in those searches. This is **not** a global novelty claim. Adjacent work still exists in assumption surfacing, specification validation, agent dry-run/policy gates, and general falsification protocols.

The retained boundary therefore remains deliberately narrow:

> a coding plan's repository-specific premise must compile into an allowlisted executable probe; a deterministic tri-state result controls a hard source-write interlock; contradicted/unknown load-bearing premises force evidence-bound replanning before patch generation.

If a public project with this same end-to-end boundary is found later, the topic must be re-audited before portfolio submission.


## Gate 4 re-audit after coding-agent preflight

The project was searched again using combinations of:

- `coding agent preflight gate repository assumptions`;
- `AI coding preflight repository assumptions`;
- `coding agent executable assumption probe`;
- `pre-code repository verification agent CLI`;
- `coding agent source write interlock`.

No directly matching GitHub repository appeared in those searches. The integration layer therefore remains vendor-neutral rather than becoming a Claude/Cursor/Codex-specific prompt skill. This is still not a global novelty claim.

The retained distinction is that a coding client may request a preflight, but only allowlisted repository probes can produce the evidence-backed tri-state verdict that controls source-write permission.
