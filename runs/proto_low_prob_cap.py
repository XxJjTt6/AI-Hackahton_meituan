#!/usr/bin/env python3
import sys,itertools,math,time,hashlib
from pathlib import Path
sys.path.insert(0,'.'); sys.path.insert(0,'runs')
import solver,proxy_eval
text=Path('runs/official_calibrated_low_synth.txt').read_text(); rows,tasks,couriers=proxy_eval.parse(text); tasks=sorted(tasks); T=set(tasks)
base=solver.solve(text); basec=solver._solution_expected_cost(base,rows,T)
print('base',round(basec,6))
by={t:[] for t in tasks}
for r in rows:
 if len(r[1])==1: by[r[1][0]].append(r)
for alpha in [0,5,20]:
 opts=[]
 for t in tasks:
  arr=[]
  rs=by[t]
  for a,b in itertools.combinations(rs,2):
   cost=solver._group_expected_cost([a,b],1); p=1-(1-a[4])*(1-b[4]); val=cost-alpha*p
   arr.append((val,cost,t,a[2],b[2]))
  opts.append(sorted(arr)[:35])
 # beam minimize val then evaluate true cost
 states={(0,): (0.0,0.0,())}
 for i,t in enumerate(tasks):
  ns={}
  for (mask,),(vsum,csum,path) in states.items():
   for val,cost,tt,a,b in opts[i]:
    ia=int(a[1:]); ib=int(b[1:]); bits=(1<<ia)|(1<<ib)
    if mask&bits: continue
    key=(mask|bits,); nv=vsum+val
    if nv<ns.get(key,(1e99,0,None))[0]: ns[key]=(nv,csum+cost,path+((tt,(a,b)),))
  states=dict(sorted(ns.items(),key=lambda kv:kv[1][0])[:400])
 best=min(states.values(),key=lambda x:x[1]) if states else None
 if best:
  res=[(t,list(cs)) for t,cs in best[2]]; print('alpha',alpha,'cost',round(solver._solution_expected_cost(res,rows,T),6),'sig',hashlib.sha256(str(res).encode()).hexdigest()[:10])
