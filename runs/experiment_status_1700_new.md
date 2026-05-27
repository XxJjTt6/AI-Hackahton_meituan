# Status 2026-05-19 17:00 CST

- Official best: `706.4522`, remaining attempts `7`.
- Reflection: rank-2 at ~700 likely found a structural objective/cost-model correction or a bottleneck-case exact solver, not tiny official-column swaps.
- Major new clue: official detail costs are much closer to `expected_score + 80*(1-p_complete)*tasks` than the solver's internal `100` failure penalty. Public `large_seed301` proxy improves drastically under global penalty 70/80/90 candidates.
- Held candidates:
  - Low-risk: `runs/candidate_large302_guard_work.py`, predicted avg `~706.4264`, preflight OK.
  - High-risk/high-upside: `runs/candidate_penalty80.py`, SHA `f9a8e9cc`, public proxy improves by ~20 but changes global behavior, especially hard cases unknown.
- Do not submit `candidate_nonhard_penalty80.py`; it is broken by text patch indentation.
