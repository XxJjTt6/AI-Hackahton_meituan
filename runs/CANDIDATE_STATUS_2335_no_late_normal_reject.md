# Candidate no late normal repair — rejected

- Candidate: `runs/candidate_no_late_normal_current_safe.py` from current safe `41db4b34`, removing the two final `_normal_worst_related_repair_solution` calls.
- Evidence: Under current high system load, safe baseline itself showed bad public-large signatures, and the no-late-normal candidate also showed bad signatures (`681.150603`, `682.189827`) before one good run.
- Decision: Do not merge or submit. It is not a structural score improvement and does not reliably solve large runtime/signature wobble.
