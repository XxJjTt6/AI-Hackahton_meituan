# 2026-05-20 97eced0c 官方失败记录

- Candidate: `runs/candidate_scarce_cache_missing_swap2_safe_20260520.py`
- SHA: `97eced0cb7284f226d9f58bbe1f934cb5283fb011c0a8b05077c2e44e653adce`
- Official avg: `711.9778`, worse than best `706.197`
- Low501 unchanged: `1799.9031`
- Scarce401 regressed: `1531.5317 -> 1589.3393`
- Scarce detail: assigned `38/40`, missing `T0028,T0033`, penalty `200`
- Observed bad structure: `T0013,T0039` received `C013,C000`; old T0033 still uncovered.
- Decision: blacklist this candidate and descendants. Do not submit missing-task swap/split cache variants without exact local replay proving 40/40 coverage on actual official rows.
- Current `solver.py` remains best SHA `70222083707d786011d28d7cc1ceab8f3b2ca95e0924b26f8dff2e6a49e865d6`, size `78516`.
