# 2026-05-20 13:36 status

- Current official best: `706.1970`, file `solver.py`, SHA `70222083`.
- Confirmed improvement: high_noise `490.0466 -> 487.7525`; all other cases unchanged from safe `41db4b34`.
- Today probes used:
  - scarce no-cache: no-op
  - scarce T0033 guarded: no-op
  - low mixed and reverse: worse, but discovered low-only guard `e < .20`
  - feature buckets: identified low bucket; avg_score not useful
  - low K2 samples/regret/extra column: no improvement or worse
  - scarce pair sample: no-op
- Remaining official attempts after last submit response: 7.
- Known official column recomposition for high/low/scarce remains saturated at current best.
