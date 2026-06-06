#!/usr/bin/env python3
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
base=(ROOT/'solver.py').read_text()
OUT=ROOT/'runs/safe_non_scarce'
OUT.mkdir(exist_ok=True)
variants=[]
# Normal only time tweaks around final related repair, never active for scarce/low.
repls=[
('normal_related_055_085', "if 9<=L<=35 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.45))", "if 9<=L<=35 and not G and not F and time.monotonic()<A-.80:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.55))"),
('normal_related_065_095', "if 9<=L<=35 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.45))", "if 9<=L<=35 and not G and not F and time.monotonic()<A-.70:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.65))"),
('normal_alns_k4', "D=_column_alns_repair_solution(D,C,B,min(A,time.monotonic()+.62),mode='normal',max_window_tasks=10,top_riders_per_task_key=8,option_limit=55,max_k=3)", "D=_column_alns_repair_solution(D,C,B,min(A,time.monotonic()+.62),mode='normal',max_window_tasks=10,top_riders_per_task_key=8,option_limit=55,max_k=4)"),
('tiny_more_window', "if L<=8 and time.monotonic()<A-.35:", "if L<=8 and time.monotonic()<A-.25:"),
]
for name,old,new in repls:
    s=base.replace(old,new,1)
    path=OUT/f'{name}.py'; path.write_text(s); variants.append(path)
print('\n'.join(str(p) for p in variants))
