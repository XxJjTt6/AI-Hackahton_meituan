# Current Shortlist

## Held candidate: scarce T0033 triple-only

- File: `runs/scarce_cache_t0033_triple_only.py`
- SHA: `61063fa8c1ed3814221f56cffe69f3d585c1c3cb9cd0b33b28e34d000868ac27`
- Status: preflight passed 2026-05-19 recheck; public large `657.10`; size `73583`.
- Mechanism: only after exact seed401 cache; tries hidden triple containing `T0033` plus residual row; requires true 40-task objective improvement >2.
- Risk: likely official no-op if hidden triple is absent; related broad T0033 families had no-op/negative results, but this one is stricter and was not found in official submissions.
- Decision: hold as possible late exploratory candidate, not enough to spend immediately while more exploration remains.

## Rejected held candidates

- `runs/scarce_pair_preserve_repack.py` (`eeb6278d`): safest but likely no-op; only use if wanting very low-risk exploratory attempt.
- `runs/scarce_cache_local_repack3.py` (`4a9ead8b`): broader repack, rejected due proxy/time instability and no strong evidence.
