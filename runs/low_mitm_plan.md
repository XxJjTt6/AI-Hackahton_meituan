# Low K=2 MITM Plan

Goal: exact-ish assignment for low: choose one 2-courier group per task, no courier reused.

Problem size: 30 tasks, 60 couriers. Top pair options per task maybe 10-20.

MITM idea:
- Split tasks 15/15.
- Enumerate top states per half with courier mask and cost, pruning dominated masks.
- Merge disjoint masks.

Risk:
- In official low, all historical pair options form exactly one feasible full matching from known columns, so hidden new benefit requires generating pair options not yet official-observed.
- Without hidden input, MITM can only help if embedded in solver and run on hidden candidates. Python size/time likely hard but possible if top pairs are small.

No official submit until standalone public/synthetic demonstrates large stable improvement and runtime <2s for low branch.
