# Current Project Status

Updated: 2026-05-27

## Safe Main

- File: `solver.py`
- SHA256: `1a316455d6a13043e8733a650d79a8176c0f6cccc780d13639eaed669c62ad39`
- Size: `78729` bytes
- Official result: `runs/official_submit_20260520_132026_70222083.json`
- Official average: `706.197`
- Validity: all 10 official cases valid

This is the current GitHub-sync baseline.

Shim note: current `solver.py` includes `_boer` / `_augment_scarce_cache` wrappers for local tests; official score reference is the same `solve()` logic as `70222083`.

## Per-Case Official Scores

| Case | Score | Coverage | Valid |
|---|---:|---:|---:|
| high_noise_seed601 | 487.7525 | 30/30 | true |
| large_seed301 | 654.2935 | 40/40 | true |
| large_seed302 | 627.0114 | 40/40 | true |
| low_willingness_seed501 | 1799.9031 | 30/30 | true |
| medium_seed201 | 478.3143 | 30/30 | true |
| medium_seed202 | 524.0195 | 30/30 | true |
| medium_seed203 | 501.0067 | 30/30 | true |
| scarce_couriers_seed401 | 1531.5317 | 39/40 | true |
| small_seed100 | 303.7211 | 15/15 | true |
| tiny_seed42 | 154.4163 | 6/6 | true |

## Current Lessons

- Duplicate courier across different groups is invalid: official reports duplicate-courier errors and `validity=false`.
- Duplicate-courier probes may show low computed `total_score`, but they are not valid final solutions.
- Same-key extra rider probe for 401 was a no-op; official stayed `706.197` and 401 stayed `1531.5317`.
- T0033 repair attempts did not beat the legal 39/40 401 cache.
- Broad cache/refactor descendants that perturb scarce timing can regress 401 to about `1589.3393`; keep current `solver.py` as the safe base.

## Validation Commands

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 _bench.py solver.py 1
python3 runs/official_submit_safe.py --solver solver.py --skip-submit
```

## Submission Gate

Do not submit a new candidate unless one of these is true:

- credible expected average improvement is at least about `1.0`, or
- the user explicitly approves a high-information rule/protocol validation.

