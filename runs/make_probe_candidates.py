from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
s=(ROOT/'solver.py').read_text()
probes={}
# Use official baseline as base; targeted single edits only.
probes['time_860']=s.replace('A=i+8.7','A=i+8.6',1).replace('if f:A=i+8.85','if f:A=i+8.75',1)
probes['time_880']=s.replace('A=i+8.7','A=i+8.8',1).replace('if f:A=i+8.85','if f:A=i+8.95',1)
probes['scarce_no_late_alns']=s.replace('if time.monotonic()<A-.85:D=_column_alns_repair_solution(D,C,B,min(A,time.monotonic()+.75),mode=_J,max_window_tasks=12,top_riders_per_task_key=8,option_limit=55,max_k=4);D=_drop_unprofitable_groups(D,C,B)','if _D and time.monotonic()<A-.85:D=_column_alns_repair_solution(D,C,B,min(A,time.monotonic()+.75),mode=_J,max_window_tasks=12,top_riders_per_task_key=8,option_limit=55,max_k=4);D=_drop_unprofitable_groups(D,C,B)',1)
probes['scarce_skip_eject_shift']=s.replace('if time.monotonic()<A-.24:\n\t\t\tA0=_scarce_eject_extra_to_uncovered(D,C,B,min(A,time.monotonic()+.18))\n\t\t\tif _solution_expected_cost(A0,C,B)<_solution_expected_cost(D,C,B)-1e-09:D=A0;D=_drop_unprofitable_groups(D,C,B)\n\t\tif time.monotonic()<A-.22:\n\t\t\tA1=_shift_couriers_between_groups(D,C,B,min(A,time.monotonic()+.18),max_moves=18)\n\t\t\tif _solution_expected_cost(A1,C,B)<_solution_expected_cost(D,C,B)-1e-09:D=_drop_unprofitable_groups(A1,C,B)','if _D and time.monotonic()<A-.24:\n\t\t\tpass',1)
probes['normal_more_time_guard']=s.replace('if 9<=L<=35 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.45))\n\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))','if 9<=L<=35 and not G and not F and time.monotonic()<A-.65:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.35))\n\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.75:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.55))',1)
probes['no_final_local_pair_rewire_g']=s.replace('if time.monotonic()<A-.18:D=_local_improve_mixed_solution(D,C,B,A,include_pair_rewire=G)','if time.monotonic()<A-.18:D=_local_improve_mixed_solution(D,C,B,A,include_pair_rewire=_D)',1)
for name,text in probes.items():
    p=ROOT/'runs'/f'probe_{name}.py'; p.write_text(text); print(p)
