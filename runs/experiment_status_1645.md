# Experiment Status 2026-05-19 16:45 CST

## What changed since 15:30

- Promoted confirmed conclusions to `AGENTS.md`: do not repeat k2 forcing, T0033 coverage forcing, or picker-only changes.
- Traced low picker: current best candidate is actually best in local pool; picker conservatism is not the bottleneck.
- Tested low local exchange diagnostics on single-task low proxy:
  - 2-opt across task groups: best gain 0.
  - 3-opt among worst 8 groups: best gain 0.
  - completion-probability-first and k<=2 multi-order greedy are worse.
- Scarce official best has exactly one signature across 24 submissions; known 40/40 solution is a near-global repack and much worse.

## Submission decision

Still no official submission. Current evidence says the project is at a local plateau; spending a submission on any current candidate would likely be no-op or negative.

## Next direction

Need a genuinely new constructive model, not local postprocessing: possible directions include deeper column generation with reduced costs, or learning a hidden-case-specific low/scarce generator from official detail patterns. These must remain size/runtime safe and dependency-free.
