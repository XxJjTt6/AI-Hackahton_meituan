#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'runs'))
import solver, proxy_eval
for scale in [.2,.25,.3,.35]:
 text=proxy_eval.make_low(scale); rows,tasks,c=proxy_eval.parse(text); T=set(tasks); out=solver.solve(text); base=solver._solution_expected_cost(out,rows,T); best=base; desc=None
 for i,(k,cs) in enumerate(out):
  if len(cs)<=1: continue
  for c in cs:
   ncs=[x for x in cs if x!=c]
   cand=out[:i]+[(k,ncs)]+out[i+1:]
   cost=solver._solution_expected_cost(cand,rows,T)
   if cost<best: best=cost; desc=(k,c)
 print(scale,base,best,desc)
