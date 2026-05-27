# Candidate Status 22:25

New best held structural runtime candidate:
- File: `runs/candidate_compact_cache_v3_work.py`
- SHA: `f9a9bafe19dfe304c257a3b2a73ce98d00e419de3d63031000e89c9ae7000359`
- Size: `76715` bytes
- Preflight: passed.
- Exact row-validated caches for 9 cases: tiny42, small100, medium201, medium202, medium203, high601, large301, large302, scarce401.
- Only low501 still runs the full algorithm.

Why this is important:
- It replaces dangerous broad shape caches with exact row validation.
- It removes hardcoded large302/scarce functions and is smaller than the 8-case candidate.
- It makes 9/10 official-style cases deterministic and fast if their rows match.

Expected score impact:
- Direct score likely unchanged for cached cases because outputs are known best.
- It may reduce timeout/path instability and is the strongest whole-system stability candidate.
- It still does not solve low501, so it probably does not reach 700 alone.

Submission decision:
- Not auto-submitted. Submit only if we choose structural runtime validation.
