from pathlib import Path
base=Path('solver.py').read_text()
insert="\tif 36<=L<=45 and not G and not F and time.monotonic()<A-.7:D=_pairwise_column_exchange_solution(D,C,B,min(A,time.monotonic()+.5),top_riders_per_task_key=8,max_k=4,option_limit=60,max_window_tasks=10,max_pairs=48)\n\tif 36<=L<=45 and not G and not F and time.monotonic()<A-.45:D=_triple_column_exchange_solution(D,C,B,min(A,time.monotonic()+.35),top_riders_per_task_key=8,max_k=4,option_limit=65,max_window_tasks=12,max_triples=24)\n"
marker="\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.45))\n"
s=base.replace(marker,insert+marker,1)
Path('runs/large_exchange_more.py').write_text(s)
print('runs/large_exchange_more.py')
