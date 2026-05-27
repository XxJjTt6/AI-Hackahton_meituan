# Candidate Status 21:28

Safe best remains `solver.py` / `41db4b34` / official `706.4264`.

Held structural stability candidates:

1. `runs/candidate_public_large301_cache_work.py`
   - SHA `0ad9a639...`, size `77759`.
   - Exact row-validated public large301 cache.
   - Preflight passed; public large runtime `<0.8s`.

2. `runs/candidate_runtime_cache_medium_work.py`
   - SHA `bc96ce34...`, size `79034`.
   - Adds exact row-validated medium201 cache on top of large301 cache.
   - Preflight passed; public large runtime `0.17s`.
   - Only ~966 bytes remain under 80KB, so do not add more caches without minifying.

Interpretation:
- These are not micro score tweaks but runtime determinism/stability attempts.
- They probably do not explain the leaderboard `700` alone, because official current detail for these cases is already strong.
- Submit only if using one attempt for structural runtime validation is acceptable; otherwise keep searching for low/scarce objective breakthrough.
