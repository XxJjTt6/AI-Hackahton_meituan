# Submission spend around 2026-05-21 24:00

Used two high-information attempts per user request:

1. `d4b140d8` / `runs/candidate_normal_augmenting_path_forced.py`
   - Result: `706.4264`
   - Signal: normal augmenting path hurts `high_noise_seed601` (`487.7525 -> 490.0466`) while other cases stay unchanged.
   - Decision: do not submit forced/global augmenting-path again; future version must be high-noise gated.

2. `797daba9` / `runs/candidate_scarce401_nearmiss_upgrade_min.py`
   - Result: `711.9778`
   - Signal: near-miss 401 probe activates known bad scarce structure (`1531.5317 -> 1589.3393`).
   - Decision: blacklist this 401 probe family.

Submission response remaining counts: after first attempt `daily_remaining=9`, after second `daily_remaining=8`.
