#!/usr/bin/env python3
import sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
mod=proxy_eval.load(ROOT/'solver.py')
rows,tasks,couriers=proxy_eval.parse(proxy_eval.DATA.read_text()); keep_t=set(tasks[:30]); keep_c=set(couriers[:60]); out=[]; idx=0
for key,ts,c,sc,w,i in rows:
    if c in keep_c and len(ts)==1 and ts[0] in keep_t:
        out.append((key,ts,c,sc,max(.0001,min(.999,w*.25)),idx)); idx+=1
text=proxy_eval.serialize(out); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks); row={(r[0],r[2]):r for r in rows}
res=mod.solve(text); sel=mod._result_to_selected(res,row); base=mod._solution_expected_cost(res,rows,T)
print('base',round(base,6),hashlib.sha256(str(res).encode()).hexdigest()[:10])
best=(0,None)
keys=list(sel)
for i,a in enumerate(keys):
 for b in keys[i+1:]:
  ga,gb=sel[a],sel[b]
  if len(ga)>3 or len(gb)>3: continue
  ca=mod._group_expected_cost(ga,1); cb=mod._group_expected_cost(gb,1); old=ca+cb
  cour=[r[2] for r in ga+gb]
  # try all repartitions preserving group sizes
  import itertools
  for sa in itertools.combinations(cour,len(ga)):
   sb=[c for c in cour if c not in sa]
   na=[row.get((a,c)) for c in sa]; nb=[row.get((b,c)) for c in sb]
   if any(x is None for x in na+nb): continue
   new=mod._group_expected_cost(na,1)+mod._group_expected_cost(nb,1)
   gain=old-new
   if gain>best[0]+1e-9: best=(gain,(a,b,sa,tuple(sb),old,new))
print('best_gain',best)
