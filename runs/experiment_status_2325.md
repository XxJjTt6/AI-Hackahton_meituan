# Experiment Status 23:25

Safe main remains `solver.py` sha `41db4b34`, official avg `706.4264`.

New checks this round:
- Recomputed all official JSON case bests with correct `total_score` field.
- Historical per-case best average is only `706.1970`; safe main has only `2.2941` remaining historical gap, all from `high_noise_seed601`.
- Official detail column mining for `high/low/scarce`:
  - high recombination reaches `487.7525` only, matching known small candidate.
  - low official column recombination exactly reproduces `1799.9031` with `{2:30}`.
  - scarce pruned DP over official columns reproduces `1531.5316` with 39/40 coverage.
- `candidate_low_match_work.py` on calibrated low is exact same signature as safe main (`06842fb3c2c0`), so old K=2 matching line is no-op locally.
- `candidate_clean_high_scarce_enum.py` passes low signature but gate rejects: expected avg gain only `0.22941`, below threshold.

Decision:
- No submission. Remaining official attempts stay at 3.
- Do not spend attempts on high-only micro gain or old low matching.
- Only possible submit-worthy path remains a genuinely new low/scarce column generator with expected total gain >= 10.
