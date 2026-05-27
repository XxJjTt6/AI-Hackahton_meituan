# Candidate Status 18:32

Current safe submit file is repo-root `solver.py` only (`41db4b34`, official `706.4264`).

Do not submit:
- `candidate_p80_fast_global.py`, `candidate_penalty*.py`, `candidate_large_penalty80.py`, `candidate_nonhard_p80_safe.py`: p80/global penalty family, official negative.
- `candidate_high_guard_work.py`: official `711.9778`, scarce regression.
- `candidate_filter_lowprob.py`, `candidate_nonhard_penalty80.py`: broken/indent errors.
- `candidate_finalpick_penalty80.py`: local negative / below threshold.
- `candidate_high_guard_compact.py`: possibly valid high micro-fix, but below current threshold; save for near-700 only.

Already absorbed into safe `solver.py`:
- `candidate_medium202_direct_b8253edc.py`
- `candidate_large302_guard_work.py`

Submission policy: run `runs/submission_gate_policy.py` before any future official submit.
