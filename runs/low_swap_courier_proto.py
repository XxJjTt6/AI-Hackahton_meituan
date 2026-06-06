#!/usr/bin/env python3
import sys,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'runs'))
import solver, proxy_eval
for scale in [.25,.3]:
 text=proxy_eval.make_low(scale); rows,tasks,c=proxy_eval.parse(text); T=set(tasks); out=solver.solve(text); base=solver._solution_expected_cost(out,rows,T); best=base; desc=None
 for i in range(len(out)):
  for j in range(i+1,len(out)):
   k1,cs1=out[i]; k2,cs2=out[j]
   for a in cs1:
    for b in cs2:
     n1=[b if x==a else x for x in cs1]; n2=[a if x==b else x for x in cs2]
     cand=out[:i]+[(k1,n1)]+out[i+1:j]+[(k2,n2)]+out[j+1:]
     cost=solver._solution_expected_cost(cand,rows,T)
     if cost<best: best=cost; desc=(k1,a,k2,b)
 print(scale,base,best,desc)
