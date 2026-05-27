# Candidate Status After 60cf6691 Official Failure

Official submission:
- File: `runs/candidate_compact_cache_v6_highbest_work.py`
- SHA: `60cf6691...`
- Result: avg `836.3734`
- Catastrophic regression: `large_seed302 = 1926.4815`
- High601 did not improve; remained `490.0466`.

Decision:
- Blacklist compact cache family v3/v4/v5/v6 and descendants.
- Safe main remains repo-root `solver.py` / `41db4b34` / official `706.4264`.
- Do not try to compress/replace official-proven hardcoded cache functions again today.
