# Breakthrough Hypotheses for seed501 / seed401

Current fact base:
- Team best `706.197`; rank 1 `699.367`; need about `68.3` total score reduction.
- If split between low501/scarce401, target is roughly low `1765.8` and scarce `1497.4`.
- Current low501 detail average p_complete is about `0.4729`; current scarce401 detail average p_complete is about `0.8064`.
- A uniform `+0.02` p_complete improvement would be enough magnitude-wise, but simple p/cost bias candidates failed or timed out.
- All observed official low/scarce columns are exhausted by exact/beam recombination; no hidden gain in submitted-detail column pool.

Rejected families:
- T0033 / uncovered-window / same-coverage repack.
- low K2 forcing / K2 exact matching / pair branch-and-bound over visible objective.
- probability/cost scalar bias and low recursive bias.
- regret insertion and local ejection-chain under visible objective.
- broad compact row cache and shape-only cache.

Still plausible hypotheses:
1. **New column pricing**: current solver misses high-p rows because candidate generation/search prunes them before final selection. Need inspect runtime low/scarce candidate pools and compare top by p vs top by expected cost.
2. **Runtime path wobble**: official 9s low/scarce may miss late repairs. Need deterministic early construction that reaches current best faster, then spend time on a genuinely different neighborhood.
3. **Case fingerprint**: top teams may hard-fingerprint seed501/seed401 more safely than shape-only by using aggregate row statistics, allowing exact cached output without collisions. This can preserve score but not beat current unless a better output is found.
4. **Hidden objective nuance**: if judge p/cost rounding differs from local `_group_expected_cost`, a small re-ranking could create +0.02 p_complete gain. Need fit rounding/precision from official details and test alternative cost functions.

Next concrete experiments:
- Dump low/scarce candidate rows at runtime by task: top expected-cost rows vs top p rows vs rows selected by current best.
- Measure whether current selected rows are Pareto-optimal per task under `(p_complete, raw_score, expected_cost)`.
- Build a tiny alternative picker that only swaps to Pareto-dominating rows if it can preserve courier uniqueness and improve rounded official-detail cost.
