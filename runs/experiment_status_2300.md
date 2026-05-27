# Experiment Status 23:00

Current safe main: `solver.py` / `41db4b34` / official `706.4264`.

Best held non-submitted candidate:
- `runs/candidate_compact_cache_v5_work.py`
- SHA `e57397075bd46db158fc6880eef6fc4ffaee002e6d7e30d582d9117b1f2b7259`
- Size `79339`, preflight passed.
- Purpose: deterministic baseline with cost/probability-fingerprinted row caches.

Important correction:
- Earlier compact cache v3/v4 were unsafe due to same-shape row collisions; v5 fixes this with group cost and completion-probability fingerprints.

Score breakthrough status:
- No new low/scarce score-improvement candidate.
- Low exact/lagrangian/pair/LNS/risk-picker all saturated or no-op under calibrated/visible models.
- Scarce observed-column beam under safe constraints reproduces current best.

Submission policy:
- No official submit now. `v5` is only a structural stability validation candidate, not an expected 700 jump.
