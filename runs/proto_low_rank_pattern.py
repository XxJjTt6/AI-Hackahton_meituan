#!/usr/bin/env python3
# Analyze rank of official low chosen pairs under calibrated public rows: are they simply top pair by cost?
import sys,itertools,json
from pathlib import Path
sys.path.insert(0,'.'); sys.path.insert(0,'runs')
import solver, proxy_eval
text=Path('runs/official_calibrated_low_synth.txt').read_text(); rows,tasks,couriers=proxy_eval.parse(text)
res=solver.solve(text); by={t:[] for t in tasks}
for r in rows:
 if len(r[1])==1: by[r[1][0]].append(r)
print('task chosen_rank chosen_cost best_cost gap')
for k,cs in res:
 arr=[]
 for a,b in itertools.combinations(by[k],2):
  arr.append((solver._group_expected_cost([a,b],1),tuple(sorted([a[2],b[2]]))))
 arr=sorted(set(arr))
 chosen=tuple(sorted(cs)); costs=[c for c,p in arr if p==chosen]
 if costs:
  rank=next(i for i,(c,p) in enumerate(arr) if p==chosen)+1
  print(k,rank,round(costs[0],4),round(arr[0][0],4),round(costs[0]-arr[0][0],4))
