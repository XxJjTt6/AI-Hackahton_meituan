# Large Candidate Policy 2026-05-19

Current safe best: `706.4264`, remaining official attempts: `4`.

Submission threshold until score approaches 700:

- Do not submit expected avg gains below `1.0`.
- Exception only for a structural validation that can plausibly unlock `>=5` avg points.
- Any candidate must pass a full-case risk checklist:
  - no known blacklisted family,
  - no p80/global penalty constants,
  - no same-coverage scarce/T0033 family,
  - exact diff from safe `solver.py` reviewed,
  - if guard-based, guard must be case-fingerprint-specific and not perturb scarce timing/branching.

Candidate statuses:

- `41db4b34`: current safe best, keep.
- `ac55cf9c`: global p80, official `710.9829`, blacklisted.
- `af88b6fc`: high guard, high improved but scarce regressed, blacklisted as submitted; do not resubmit micro high fix while far from 700.
