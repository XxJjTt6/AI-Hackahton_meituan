# Night campaign 2026-05-26

Goal: improve official AutoSolver score from 706.197 to <=700 before 2026-05-27 09:00 Asia/Shanghai.

Hard submission budget from user: 12 official attempts, absolute max 15. Do not exceed 15.

Canonical starting solver for official best 706.197:
- `/Users/比赛/true_new_start_meituan/solver.py`
- `/Users/比赛/FOR_AutoSolver_706.72/runs/baselines/official_best_70222083.py`
- sha256 `70222083707d786011d28d7cc1ceab8f3b2ca95e0924b26f8dff2e6a49e865d6`

Process:
- Keep candidate solver under 80KB.
- Prefer no official submit unless credible expected average gain >=1.0.
- Record every direction and no-submit reason.

## 2026-05-26 start

- Synced research repo `solver.py` to canonical 706.197 sha `70222083...` to avoid deriving from failed equivalent reserve candidate.
- No official submissions on 2026-05-26 found at campaign start.

## Round 01 low entry/column-width sweep

Script: `runs/night_20260526/round01_low_entry_sweep.py`.
Result: no official submit. Bias recursion worsened official-like; scale/global-time tweaks did not improve official-like; wider low column search only changed synthetic/proxy behavior and did not provide credible official average gain. Some variants improved synthetic scarce40, but official scarce401 is hard-cache sensitive and this is not sufficient evidence.

## Rounds 02-05 summary

- Row ranking sweep: score/willingness/diverse row ordering did not improve official-like.
- Low larger repair windows: improved some synthetic low030/low025 samples but official-like stayed unchanged.
- SA-LNS prototype based on recent ALNS/annealing ideas improved synthetic low in some seeds but made zero improvement on official-like and calibrated proxies.
- No official submissions: none meet >=1.0 expected official average gain.
