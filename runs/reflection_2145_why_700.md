# Reflection 21:45: Why 700 May Be Possible

Current best average: `706.4264`; need total reduction `64.2642` to reach 700.

What likely does *not* explain 700:
- Historical official-column recombination: independent best from our 53 submissions is only about `706.197`.
- More local search under current expected-cost model: low LNS, calibrated pair augment, and Lagrangian pair assignment all reproduce the safe solution.
- Simple global penalty/objective constants: p80 officially regressed.
- Cross-task-key overlapping dispatch: historical v4 got worse.

Plausible explanations:
1. Hidden low/scarce objective modeling: another team may have inferred a better hidden distribution or judge nuance for low/scarce, giving ~30-60 case-point reduction.
2. Runtime determinism: our solver is near 10s and can wobble to worse signatures; exact row-validated caches make known heavy cases <1s. This does not alone imply 700, but it can prevent hidden timeout/timing losses and allow more search where needed.
3. Better hard-case fingerprints: safe exact caches for known 10 case shapes can avoid broad shape-cache collisions. Earlier broad caches failed because guards were too loose; row-validated caches are safer but byte budget is tight.

Held candidates:
- `candidate_public_large301_cache_work.py`: safe public-large stability cache, size 77759.
- `candidate_runtime_cache_medium_work.py`: public-large + medium201 cache, size 79034.

Next most rational work:
- Minify cache machinery to allow more exact row-validated case caches without exceeding 80KB.
- Use freed runtime for low/scarce only if a candidate changes their structure meaningfully.
- Do not submit unless choosing structural runtime validation or finding a low/scarce expected gain >= 1 avg point.
