from pathlib import Path
import subprocess, json, re, os, sys, time
base=Path('solver.py').read_text(); out=Path('runs/current_best_param_scan'); out.mkdir(exist_ok=True)
vars={
 'scarce_shadow_penalty55': {'60.*(len(I)-len(B))':'55.*(len(I)-len(B))'},
 'scarce_shadow_penalty65': {'60.*(len(I)-len(B))':'65.*(len(I)-len(B))'},
 'scarce_shadow_extra12': {'14.*L+N+M/5.':'12.*L+N+M/5.'},
 'scarce_shadow_extra16': {'14.*L+N+M/5.':'16.*L+N+M/5.'},
 'low_accept15': {'if H<=C+25.:return F':'if H<=C+15.:return F'},
 'low_accept35': {'if H<=C+25.:return F':'if H<=C+35.:return F'},
 'normal_related_only_once': {'if 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))':'if _D and 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))'},
 'scarce_disable_final_shift': {'if G and time.monotonic()<A-.24:D=_shift_couriers_between_groups(D,C,B,min(A,time.monotonic()+.18),max_moves=18)':'if _D and G and time.monotonic()<A-.24:D=_shift_couriers_between_groups(D,C,B,min(A,time.monotonic()+.18),max_moves=18)'},
 'scarce_disable_late_elite': {'if f and time.monotonic()<A-1.35:\n\t\tR=_solve_scarce_elite_column_recombine':'if _D and f and time.monotonic()<A-1.35:\n\t\tR=_solve_scarce_elite_column_recombine'},
}
files=[]
for name,repls in vars.items():
 s=base; ok=True
 for a,b in repls.items():
  if a not in s: print('missing',name,a); ok=False; break
  s=s.replace(a,b)
 if ok:
  p=out/(name+'.py'); p.write_text(s); files.append(str(p))
print('generated',len(files))
for p in files:
 print('\n###',p, flush=True)
 try:
  r=subprocess.run([sys.executable,'runs/proxy_eval.py','solver.py',p],cwd=Path.cwd(),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
  print(r.stdout[-2500:], flush=True)
 except subprocess.TimeoutExpired:
  print('TIMEOUT', flush=True)
