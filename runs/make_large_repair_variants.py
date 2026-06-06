from pathlib import Path
base=Path('solver.py').read_text()
variants={
'large_repair_worst40.py': "\tif 36<=L<=45 and not G and not F and time.monotonic()<A-.75:D=_repair_worst_window_solution(D,C,B,min(A,time.monotonic()+.65),top_riders_per_task_key=8,max_k=3,option_limit=55)\n",
'large_repair_alns40.py': "\tif 36<=L<=45 and not G and not F and time.monotonic()<A-.85:D=_column_alns_repair_solution(D,C,B,min(A,time.monotonic()+.75),mode='normal',max_window_tasks=10,top_riders_per_task_key=8,option_limit=55,max_k=3)\n",
'large_repair_worst_alns40.py': "\tif 36<=L<=45 and not G and not F and time.monotonic()<A-1.25:D=_repair_worst_window_solution(D,C,B,min(A,time.monotonic()+.55),top_riders_per_task_key=8,max_k=3,option_limit=55)\n\tif 36<=L<=45 and not G and not F and time.monotonic()<A-.75:D=_column_alns_repair_solution(D,C,B,min(A,time.monotonic()+.65),mode='normal',max_window_tasks=10,top_riders_per_task_key=8,option_limit=55,max_k=3)\n",
}
marker="\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.45))\n"
for name,insert in variants.items():
    s=base.replace(marker, insert+marker,1)
    p=Path('runs')/name
    p.write_text(s)
    print(p)
