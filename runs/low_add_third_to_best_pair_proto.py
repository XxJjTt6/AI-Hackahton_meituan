#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'runs'))
import solver, proxy_eval
for scale in [.2,.25,.3,.35]:
 text=proxy_eval.make_low(scale); rows,tasks,c=proxy_eval.parse(text); T=set(tasks); out=solver.solve(text); base=solver._solution_expected_cost(out,rows,T); lut={(r[0],r[2]):r for r in rows}; by={}
 for r in rows:
  if len(r[1])==1: by.setdefault(r[0],[]).append(r)
 used={c for k,cs in out for c in cs}; best=base; bestdesc=None
 for i,(k,cs) in enumerate(out):
  if ',' in k: continue
  cur=[lut[(k,c)] for c in cs if (k,c) in lut]
  for r in by.get(k,[]):
   if r[2] in used: continue
   cand=out[:i]+[(k,cs+[r[2]])]+out[i+1:]
   cost=solver._solution_expected_cost(cand,rows,T)
   if cost<best: best=cost; bestdesc=(k,r[2])
 print(scale,base,best,bestdesc)
