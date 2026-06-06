#!/usr/bin/env python3
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
base=(ROOT/'solver.py').read_text()
out=ROOT/'runs'/'operator_ablation'; out.mkdir(exist_ok=True)
variants={
 'no_normal_related_2': ("\n\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))", ""),
 'no_normal_related_all': ("\n\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.45))\n\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))", ""),
 'no_low_shift': ("\n\tif J and time.monotonic()<A-.32:D=_shift_couriers_between_groups(D,C,B,min(A,time.monotonic()+.24),max_moves=30)", ""),
 'no_low_late_accept': ("\n\tif J and time.monotonic()<A-.95:D=_low_late_acceptance_repair_solution(D,C,B,min(A,time.monotonic()+.85))", ""),
 'no_low_deep': ("\n\tif J and time.monotonic()<A-1.35:D=_low_deep_window_repair_solution(D,C,B,min(A,time.monotonic()+1.2))", ""),
}
for name,(old,new) in variants.items():
    if old not in base:
        print('missing',name)
        continue
    p=out/(name+'.py'); p.write_text(base.replace(old,new,1)); print(p)
