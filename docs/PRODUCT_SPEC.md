# PlanProbe product specification

## Product sentence

**AI coding agents must prove the repository assumptions behind their plan before they are allowed to write source code.**

PlanProbe is not a chatbot, PR summarizer, generic reviewer, or prompt-only skill. It is a pre-code execution gate:

`feature request → tentative plan → implicit assumptions → executable repository probes → block/replan → patch → independent verification`

## Core problem

Coding agents often fail after committing to a plausible but false repository premise: a timestamp policy is assumed global when it is regional, a scalar is assumed where the schema is a list, or a retry contract is presumed absent/present without evidence. Ordinary workflows discover the mistake after edits, tests, and repair loops.

PlanProbe moves that falsification step before source modification.

## Non-negotiable invariants

1. The planning model cannot mark its own premise as verified.
2. Probe execution uses a finite allowlisted DSL; no model-authored shell commands.
3. Load-bearing `contradicted` or `unknown` premises block code generation.
4. The revised plan must carry evidence IDs from executed probes.
5. Generated patches cannot edit tests, probe executors, gate policy, or CI.
6. Final acceptance uses independent checks.
7. No chat UI.

## v0.1 demo domain

A synthetic multilingual game LiveOps reward service. This is a portfolio-safe scenario and does not infer GameSpring's private systems.

Feature request: add a streak bonus while preserving regional event time behavior, multi-region requests, and retry/idempotency behavior.

The tentative plan contains two plausible false premises:
- all schedules are UTC;
- one request has a single region.

Repository probes disprove both before any source edit, the plan is rewritten from evidence, and only then is a patch generated.


## Fail-closed replan contract

- A load-bearing `unknown` premise cannot be repaired by model guesswork in v0.1; the run ends before source modification.
- A replan may cite only evidence IDs emitted by executed probes.
- Evidence attached to contradicted load-bearing premises is mandatory in the replan.
- A replan that introduces a new load-bearing premise without another probe round is rejected.

This keeps the product sentence literal: repository assumptions must be proven before source code can be written.
