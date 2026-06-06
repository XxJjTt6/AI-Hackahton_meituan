#!/usr/bin/env python3
import sys,itertools,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
mod=proxy_eval.load(ROOT/'solver.py')
rows,tasks,couriers=proxy_eval.parse(proxy_eval.DATA.read_text()); keep_t=set(tasks[:30]); keep_c=set(couriers[:60]); out=[]; idx=0
for key,ts,c,sc,w,i in rows:
 if c in keep_c and len(ts)==1 and ts[0] in keep_t: out.append((key,ts,c,sc,max(.0001,min(.999,w*.25)),idx)); idx+=1
text=proxy_eval.serialize(out); rows,tasks,couriers=proxy_eval.parse(text); T=sorted(tasks); cid={c:i for i,c in enumerate(sorted(couriers))}
base=mod.solve(text); print('base',round(mod._solution_expected_cost(base,rows,set(T)),6))
by={t:[r for r in rows if r[1][0]==t] for t in T}; opts=[]
for t in T:
 top=sorted(by[t],key=mod._single_expected_cost)[:16]; gs=[]
 for k in (1,2,3):
  for comb in itertools.combinations(top,k):
   mask=0
   for r in comb: mask|=1<<cid[r[2]]
   gs.append((mod._group_expected_cost(comb,1),mask,t,tuple(r[2] for r in comb)))
 gs=sorted(gs,key=lambda x:x[0])[:40]
 opts.append((gs[0][0],t,gs))
opts.sort(reverse=True)  # hard first
states={0:(0,[])}; deadline=time.monotonic()+5
for _,t,gs in opts:
 new=[]
 for mask,(cost,path) in states.items():
  for gc,gm,gt,cs in gs:
   if mask&gm: continue
   new.append((cost+gc,mask|gm,path+[(gt,list(cs))]))
 if not new: break
 new.sort(key=lambda x:(x[0]+100*(len(opts)-len(x[2])), x[0])); states={m:(c,p) for c,m,p in new[:6000]}
 if time.monotonic()>deadline: break
best=min(states.values(),key=lambda x:x[0])
sol=sorted(best[1])
print('beam',round(mod._solution_expected_cost(sol,rows,set(T)),6),len(sol),hashlib.sha256(str(sol).encode()).hexdigest()[:10])
