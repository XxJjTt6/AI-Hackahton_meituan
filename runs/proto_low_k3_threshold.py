#!/usr/bin/env python3
import sys,itertools,time
from pathlib import Path
sys.path.insert(0,'.'); sys.path.insert(0,'runs')
import solver, proxy_eval
text=Path('runs/official_calibrated_low_synth.txt').read_text(); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
base=solver.solve(text); print('base',solver._solution_expected_cost(base,rows,T),{k:sum(len(cs)==k for _,cs in base) for k in range(1,5)})
lut={(r[0],r[2]):r for r in rows}; by={t:[] for t in tasks}
for r in rows:
    if len(r[1])==1: by[r[1][0]].append(r)
# Start from base and greedily add 3rd courier if judge expected cost improves under calibrated low.
sel={k:[lut[(k,c)] for c in cs] for k,cs in base}
used={r[2] for v in sel.values() for r in v}
while True:
    best=None
    for t,cur in sel.items():
        if len(cur)>=3: continue
        old=solver._group_expected_cost(cur,1)
        for r in by[t]:
            if r[2] in used: continue
            new=solver._group_expected_cost(cur,1,extra=r); gain=old-new
            if best is None or gain>best[0]: best=(gain,t,r,new)
    if not best or best[0]<=1e-9: break
    gain,t,r,new=best; sel[t].append(r); used.add(r[2]); print('add',t,r[2],'gain',gain,'cost',sum(solver._group_expected_cost(v,1) for v in sel.values()))
res=[(t,[r[2] for r in v]) for t,v in sorted(sel.items())]
print('final',solver._solution_expected_cost(res,rows,T),{k:sum(len(cs)==k for _,cs in res) for k in range(1,5)})
