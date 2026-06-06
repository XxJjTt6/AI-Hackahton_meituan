#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'runs'))
import solver, proxy_eval
for scale in [.25,.3]:
 text=proxy_eval.make_low(scale); rows,tasks,c=proxy_eval.parse(text); T=set(tasks); out=solver.solve(text); lut={(r[0],r[2]):r for r in rows}; base=solver._solution_expected_cost(out,rows,T)
 groups=[]
 for idx,(k,cs) in enumerate(out):
  rr=[lut[(k,c)] for c in cs if (k,c) in lut]; groups.append((solver._group_expected_cost(rr,len(k.split(',')))/len(k.split(',')),idx,k,cs))
 high=sorted(groups,reverse=True)[:6]; low=sorted(groups)[:8]; best=base; desc=None
 for _,i,k1,cs1 in high:
  for _,j,k2,cs2 in low:
   if i==j: continue
   if i>j: i,j=j,i; k1,k2=k2,k1; cs1,cs2=cs2,cs1
   for a in cs1:
    for b in cs2:
     n1=[b if x==a else x for x in cs1]; n2=[a if x==b else x for x in cs2]
     cand=out[:i]+[(k1,n1)]+out[i+1:j]+[(k2,n2)]+out[j+1:]
     cost=solver._solution_expected_cost(cand,rows,T)
     if cost<best: best=cost; desc=(k1,a,k2,b)
 print(scale,base,best,desc)
