# Architecture

```text
Korean feature request
        │
        ▼
Tentative Planner (LLM/provider)
        │
        ▼
Implicit Premises
        │
        ▼
Probe Compiler (finite DSL proposal)
        │
        ▼
Deterministic Probe Runtime ─────► repository source/tests/config
        │
        ▼
Pre-code Gate
   ┌────┴─────┐
 block       pass
   │            │
   ▼            │
Evidence-bound Replanner
   │
   ▼
Bounded Patch Generator
   │
   ▼
Patch Allowlist
   │
   ▼
Existing contracts + acceptance checks
   │
   ▼
Evidence packet / UI
```

The model is an actor. Probe execution, gate verdicts, patch boundaries, and test verdicts are separate authorities.
