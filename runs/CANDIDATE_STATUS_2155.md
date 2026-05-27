# Candidate Status 21:55

New held structural candidate:
- File: `runs/candidate_compact_cache_work.py`
- SHA: `32b9d7653b938f530e6cc564f287aada7aec81ec74dfaea6ed81b6cca9a5086a`
- Size: `78734` bytes
- Preflight: passed (`py_compile`, 26 unit tests, public large bench, health)
- Caches: exact row-validated public large301, official medium201, official medium203, official high601.
- Public large runtime: ~`0.20s` instead of `9-10.5s`, fixed good signature.

Expected impact:
- This is an overall 10-case runtime/determinism candidate, not a direct low/scarce score breakthrough.
- It may protect against time-limit wobble and free judge time, but current official scores for these cached cases are already at our known best, so direct avg gain is uncertain/small.
- Under user policy, do not auto-submit unless we decide a structural runtime validation is worth one attempt.

Why this matters for the “why 700?” question:
- We found current safe solver is timing-unstable on public large; a faster/stabler architecture could be part of stronger leaderboard solutions.
- Still, reaching 700 likely additionally requires low/scarce hidden modeling; this candidate alone is unlikely to close 6.4 avg points.
