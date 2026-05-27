# Current Candidate Status

## Safe Main
- File: `solver.py`
- SHA: `41db4b34311c964c11fa16d650265a38a83cfea854d7aadd4cc8e72da3060951`
- Official avg: `706.4264`
- This is the only safe submit-quality file right now.

## Officially Failed / Blacklisted
- `runs/candidate_compact_cache_v6_highbest_work.py` / `60cf6691`: official avg `836.3734`, large302 `1926.4815`.
- All compact row-cache descendants v3/v4/v5/v6: banned due hidden same-shape collisions.
- `runs/candidate_clean_low_extra_branch.py`: no-op and slower.

## Remaining Attempts
- 3, based on submit response after `60cf6691`.

## Submission Gate
- `runs/submission_gate_policy.py` now rejects compact row-cache family and blacklisted SHA prefixes.
- Future submission requires clean diff from safe main and expected avg gain >= 1.0, unless user explicitly approves another structural validation.
