from pathlib import Path
base=Path('solver.py').read_text(); out=Path('runs/medium_less_post'); out.mkdir(exist_ok=True)
vars={
 'no_normal_related2': {"if 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))":"if _D and 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))"},
 'no_normal_related_all': {"if 9<=L<=35 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.45))":"if _D and 9<=L<=35 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution(D,C,B(min(A,time.monotonic()+.45)))"},
 'no_normal_alns': {"if 9<=L<=35 and not G and not F and time.monotonic()<A-.75:\n\t\tD=_column_alns_repair_solution":"if _D and 9<=L<=35 and not G and not F and time.monotonic()<A-.75:\n\t\tD=_column_alns_repair_solution"},
 'normal_skip_final_reassign': {"if time.monotonic()<A-.22:\n\t\tK=_reassign_mixed_solution(D,C,B,min(A,time.monotonic()+.35))":"if G and time.monotonic()<A-.22:\n\t\tK=_reassign_mixed_solution(D,C,B,min(A,time.monotonic()+.35))"},
}
for name,mp in vars.items():
 s=base; ok=True
 for a,b in mp.items():
  if a not in s: print('missing',name,a[:40]); ok=False; break
  s=s.replace(a,b)
 if ok:
  p=out/(name+'.py'); p.write_text(s); print(p)
