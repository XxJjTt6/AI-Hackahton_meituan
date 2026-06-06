#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
base=(ROOT/'solver.py').read_text()
changes={
 'sparse_less_trigger': ("if G and AE<len(B)-1 and time.monotonic()<A-.9:", "if G and AE<len(B)-2 and time.monotonic()<A-.9:"),
 'skip_final_colalns_scarce': ("if time.monotonic()<A-.85:D=_column_alns_repair_solution(D,C,B,min(A,time.monotonic()+.75),mode=_J,max_window_tasks=12,top_riders_per_task_key=8,option_limit=55,max_k=4);D=_drop_unprofitable_groups(D,C,B)", "if _D and time.monotonic()<A-.85:D=_column_alns_repair_solution(D,C,B,min(A,time.monotonic()+.75),mode=_J,max_window_tasks=12,top_riders_per_task_key=8,option_limit=55,max_k=4);D=_drop_unprofitable_groups(D,C,B)"),
 'more_final_reassign_time': ("if time.monotonic()<D-.22:\n\t\tI=_reassign_mixed_solution(A,B,C,min(D,time.monotonic()+.35))", "if time.monotonic()<D-.30:\n\t\tI=_reassign_mixed_solution(A,B,C,min(D,time.monotonic()+.50))"),
}
for name,(old,new) in changes.items():
    s=base
    if old not in s:
        print('missing',name); continue
    p=ROOT/'runs'/f'{name}.py'
    p.write_text(s.replace(old,new,1))
    print('###',name,p)
    subprocess.run([sys.executable, str(ROOT/'runs/proxy_eval.py'), str(p.relative_to(ROOT))], check=False)
