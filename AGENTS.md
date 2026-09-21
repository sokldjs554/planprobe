# PlanProbe agent contract

PlanProbe treats coding models as proposal generators, not verification authorities.

Hard rules:
- Never let model output directly execute arbitrary shell commands.
- Never let a model mark its own assumption as verified.
- Verification fixtures and probe executors are outside the patchable surface.
- A load-bearing `contradicted` or `unknown` premise blocks code generation.
- Code generation is allowed only after a revised plan references resolved evidence IDs.
- Keep the browser UI non-chat: request form, plan, assumptions, probes, evidence, diff, checks.
- Do not claim an external model was run unless a run artifact proves it.
- Do not weaken tests or gates to make a generated patch pass.
