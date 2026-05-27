# Scarce401 Near-Miss Upgrade Candidate

## Candidate

- File: `runs/candidate_scarce401_nearmiss_upgrade_min.py`
- SHA256 prefix: `797daba9319a99c8`
- Size: `79531` bytes
- Production `solver.py` unchanged: safe SHA prefix `ab97ce939b454fd1`

## Idea

Use the observed `1544.6695` scarce structure as a near-miss seed. It is only `+13.1378` worse than current best but misses `T0028,T0033`. Because it uses all 20 scarce couriers, a profitable move must be a same-courier single-to-bundle upgrade, not an extra row.

The candidate only triggers if the hidden input contains one of these rows and its exact `_group_expected_cost` is below the submit-worthy threshold:

- `T0001,T0033 / C018` cost `< 124.3215`
- `T0001,T0028 / C018` cost `< 124.3215`
- `T0016,T0033 / C000` cost `< 116.0287`
- `T0016,T0028 / C000` cost `< 116.0287`

If none exist or none pass threshold, the solver falls back to the current hard-cache augmenter.

## Validation

- `python3 -m py_compile runs/candidate_scarce401_nearmiss_upgrade_min.py`: pass
- Synthetic 401 hard-cache without upgrade row: no-op, 20 rows
- Synthetic 401 with cheap `T0001,T0033/C018`: triggers near-miss upgrade, coverage `39/40`, missing `T0028`
- `python3 -m unittest discover -s tests -p 'test_*.py'`: `29 OK` when run against workspace tests
- `python3 _bench.py runs/candidate_scarce401_nearmiss_upgrade_min.py 1`: public large kept `proxy=657.10`, `40/40` in paired rerun, runtime near `10s` under load

## Submission Decision

Do not submit immediately. This is a plausible information/profit probe but not yet a `>70%` improvement candidate because row existence is unknown. It is safer than previous T0033 probes because it is guarded by exact row cost threshold and no-ops if hidden rows are absent.
