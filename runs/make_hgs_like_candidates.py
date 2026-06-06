#!/usr/bin/env python3
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
base=(ROOT/'solver.py').read_text()
out=ROOT/'runs'
# Conservative SREX-lite: after choosing D from E, run an extra hard-scarce polish candidate only when scarce and enough time.
# Implemented as selecting best of D and a re-polished version with baseline operators, no enlarged pair pool.
s=base
old="""\tif G and time.monotonic()<A-.3:\n\t\tD=_reassign_mixed_solution(D,C,B,A);D=_drop_unprofitable_groups(D,C,B)"""
new="""\tif G and time.monotonic()<A-.58:\n\t\tR=_scarce_polish_candidate(D,C,B,min(A,time.monotonic()+.42))\n\t\tif _solution_covered_count(R,C)>=_solution_covered_count(D,C)and _solution_expected_cost(R,C,B)<_solution_expected_cost(D,C,B)-1e-09:D=R\n\tif G and time.monotonic()<A-.3:\n\t\tD=_reassign_mixed_solution(D,C,B,A);D=_drop_unprofitable_groups(D,C,B)"""
(out/'hgs_srexlite_repolish.py').write_text(s.replace(old,new,1))
# Conservative coverage-first pick only for hard scarce: prefer more coverage before cost, but preserve candidate set.
s=base
old="""\treturn min(E,key=lambda s:(_hard_scarce_shadow_cost(s,B,C),_solution_expected_cost(s,B,C)))"""
new="""\treturn min(E,key=lambda s:(-_solution_covered_count(s,B),_hard_scarce_shadow_cost(s,B,C),_solution_expected_cost(s,B,C)))"""
(out/'hgs_coverage_first_picker.py').write_text(s.replace(old,new,1))
# More granular normal/large local search only: skip scarce/low impact by gating not G/F/J.
s=base
old="""\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.45))"""
new="""\tif 9<=L<=35 and not G and not F and not J and time.monotonic()<A-.75:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.55))"""
(out/'hgs_normal_granular_more.py').write_text(s.replace(old,new,1))
for p in sorted(out.glob('hgs_*.py')): print(p)
