# PlanProbe coding rules

Before editing implementation code, read `docs/PRODUCT_SPEC.md`, `docs/COLLISION_AUDIT.md`, and `docs/JD_TRACEABILITY.md`.

Completion gate:
1. `python -m pytest -q`
2. `python -m ruff check planprobe tests`
3. `python -m mypy planprobe`
4. `python -m planprobe.cli demo > /tmp/planprobe-packet.json`
5. Confirm the first gate blocks before any patch, the revised plan is evidence-backed, and final verification passes.

Never edit synthetic target tests from the generated patch path. Never represent the deterministic demo route as an LLM quality benchmark.
