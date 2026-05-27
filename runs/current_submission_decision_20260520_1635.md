# Current Submission Decision 2026-05-20 16:35

Decision: **do not submit yet**.

Current official best baseline:
- `solver.py` SHA `70222083707d786011d28d7cc1ceab8f3b2ca95e0924b26f8dff2e6a49e865d6`
- Official avg `706.197`

Why no submit:
- Historical official per-case recomposition is exhausted: current baseline is best observed for all 10 cases.
- Low structural scans on calibrated low (`window grid`, `2/3-task exchange`, `K2 pair BB`, `K2 MCF`, `model sensitivity`) did not beat current baseline.
- Scarce T0033/window/repack failed officially (`0fc08e17`) and is blacklisted.
- Same-coverage scarce repack family has official negative history and proxy exact same-coverage beam found no reliable gain.
- No candidate currently has credible expected average improvement `>= 1.0`.

Next iteration direction:
- Do not spend official attempts on micro guards or low K2 variants.
- Search for a genuinely new hidden-instance/scoring insight, or a safe algorithm replacement that changes low/scarce by at least 10 total score with no other case risk.
