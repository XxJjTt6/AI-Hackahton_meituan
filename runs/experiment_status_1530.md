# Experiment Status 2026-05-19 15:30 CST

## Current decision

No official submission. Remaining opportunities should be preserved until a candidate is non-no-op in isolated cold-process checks or has strong official-shape evidence.

## Key discoveries since 14:58

- `runs/isolated_compare.py` added: cold-process comparisons are more trustworthy than same-process gate because low/scarce signatures differ under warm cache/timing.
- `runs/repeat_sig_matrix.py` showed same-process low025 can stabilize at a better local signature, but isolated cold-process low025 returns the baseline signature; official submissions are closer to cold-process behavior.
- `runs/scarce_no_final_shift.py` was sampled and rejected: local scarce proxy remains unstable and does not reliably improve.
- Official case-wise best is already mostly represented by current `solver.py` hidden-shape caches/upgrades; no obvious safe case-wise splice remains.

## Active bottleneck

Need a genuinely new low501/scarce401 hidden-column structure. Reweighting, pair beam assignment, k2 global search, and timing-only scarce stabilization have not produced a submit-worthy candidate.
