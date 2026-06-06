#!/usr/bin/env python3
import sys,itertools,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'runs'))
import solver, proxy_eval

def proto(text):
 rows,tasks,c=proxy_eval.parse(text); T=set(tasks); out=solver.solve(text); base=solver._solution_expected_cost(out,rows,T); best=base
 lut={(r[0],r[2]):r for r in rows}; singles={}; bundles={}
 for r in rows:
  (singles if len(r[1])==1 else bundles).setdefault(r[0],[]).append(r)
 for i,(k,cs) in enumerate(out):
  ts=k.split(',')
  if len(ts)!=2: continue
  for t_keep,t_split in [(ts[0],ts[1]),(ts[1],ts[0])]:
   fixed=out[:i]+out[i+1:]
   used={c for kk,cc in fixed for c in cc}
   # new keep group single, split group single
   opts=[]
   for t in [t_keep,t_split]:
    pool=sorted([r for r in singles.get(t,[]) if r[2] not in used], key=lambda r: solver._single_expected_cost(r))[:10]
    oo=[]
    for m in (1,2,3):
     for comb in itertools.combinations(pool,m): oo.append((solver._group_expected_cost(comb,1),t,tuple(r[2] for r in comb)))
    opts.append(sorted(oo)[:5])
   for a in opts[0]:
    for b in opts[1]:
     if set(a[2])&set(b[2]): continue
     cand=fixed+[(a[1],list(a[2])),(b[1],list(b[2]))]
     cost=solver._solution_expected_cost(cand,rows,T)
     if cost<best: best=cost
 return base,best
for scale in [.2,.25,.3,.35]: print(scale, proto(proxy_eval.make_low(scale)))
