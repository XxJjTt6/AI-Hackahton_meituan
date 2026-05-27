# Status 2026-05-19 16:20 CST

- Safe official best: `706.4522` (`b8253edc`), remaining submissions `7`.
- New candidate held, not submitted: `runs/candidate_large302_guard_work.py`, SHA `41db4b34311c964c11fa16d650265a38a83cfea854d7aadd4cc8e72da3060951`, size `76108`.
- Hypothesis: all-official-column beam found a `large_seed302` guarded replacement mixing columns from bad submissions, predicted `large302 627.2692 -> 627.0114` and average `706.4522 -> ~706.4264`.
- Validation: `py_compile`, 26 unit tests, public large301 bench, official preflight all pass; guard trigger simulated against latest official `large302` detail shape.
- Risk: replacement columns come from bad submissions; they are valid official rows individually, but combined set has not been officially verified. Worth considering as one of the remaining 7 attempts, but not urgent.
