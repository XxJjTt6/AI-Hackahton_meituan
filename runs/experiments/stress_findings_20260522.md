# Stress findings 2026-05-22

Generated public-large-derived variants across task/courier ratio, willingness scale, and bundle score scale.

Key weakness found:
- 40 tasks / 40 couriers with low willingness (`wscale=0.22/0.30`) runs over 10s locally and covers only 36-37 tasks.
- Official scarce401 is 40/40 but average willingness is not as low; however this indicates hard-scarce branch has runtime-risk and under-coverage in low-w scarce hybrids.
- 30/60 low-like variants are generally strong versus K2 top-w; current solver beats simple baselines substantially.

Next targeted algorithm idea:
- add a cheap early hard-scarce fallback/selector based on bundle MCF or sparse greedy when `G and e < threshold`, to avoid long hard-scarce polish paths causing timeout/undercoverage.
- must not perturb official 401 cache; robust cache returns before branch, so this mainly helps unseen/generated scarce-like cases and may not improve current 10 official cases unless official 401 cache misses.
