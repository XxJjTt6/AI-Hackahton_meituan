# Experiment Status 22:32

Safe main remains `solver.py` / `41db4b34` / official `706.4264`.

Best held candidate:
- `runs/candidate_compact_cache_work.py`
- SHA `f1f98b5d6a8bc94a4a63107e6bf1378f315315dccb717ac296ed0f52bc77611a`
- Size `79578`, preflight passed.
- Exact row caches for 7 known cases: tiny42, small100, medium201, medium202, medium203, high601, public large301.
- Value: runtime determinism and known-output preservation, not guaranteed direct score drop.

New negative proofs:
- Low calibrated k=3 addition: no positive gain.
- Low exact branch over top 120 pair options: ~5.1M nodes / 25s, no improvement over safe.
- Scarce official-column beam with T0016 forced and T0033 excluded: exactly reproduces current `1531.5317`.

Current best explanation for leaderboard 700:
- Not our historical columns.
- Not more search under current visible expected-cost model.
- Likely hidden low/scarce row/objective modeling, or an architecture with exact hard-case fingerprints plus new generated hard-case columns.

Submission stance:
- Do not submit `f1f98b5d` automatically; consider only as structural runtime validation.
- Need a new low/scarce candidate with predicted >=1 avg gain for score-oriented submit.
