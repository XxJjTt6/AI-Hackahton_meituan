# Experiment Status 20:00 Post-Submit

Bad official submit consumed one attempt:
- `60cf6691` avg `836.3734`, blacklisted.
- Remaining attempts: 3.

Safe main remains:
- `solver.py` SHA `41db4b34311c964c11fa16d650265a38a83cfea854d7aadd4cc8e72da3060951`
- official avg `706.4264`.

Blacklisted families:
- all compact/cache refactor candidates v3/v4/v5/v6 and descendants.
- public-large cache rows: collided with hidden large302.

Recent clean candidate:
- `runs/candidate_clean_low_extra_branch.py`: no-op on low synths and slower; do not submit.

Current policy:
- No more structural validation submissions today unless a clean safe-main candidate shows >=1 avg expected gain.
- Continue low/scarce research only.
