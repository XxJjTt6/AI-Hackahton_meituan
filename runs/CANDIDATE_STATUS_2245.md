# Candidate Status 22:45

Best held deterministic baseline candidate after collision fix:
- File: `runs/candidate_compact_cache_v5_work.py`
- SHA: `e57397075bd46db158fc6880eef6fc4ffaee002e6d7e30d582d9117b1f2b7259`
- Size: `79339` bytes
- Preflight: passed.
- Exact row caches with group cost / completion-probability fingerprint, preventing same-shape row collisions.
- Verified on `official_calibrated_low_synth.txt`: no false medium-cache hit; it runs low algorithm and returns safe calibrated low signature.

Supersedes:
- `candidate_compact_cache_v3_work.py` and `v4_work.py` are unsafe because selected-row-only validation can collide across same-shape 30/60 inputs.

Expected impact:
- Deterministic baseline / runtime validation, not direct score breakthrough.
- Safer than v3/v4; still not auto-submit under no-micro policy.
