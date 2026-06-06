#!/usr/bin/env python3
import sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
mod=proxy_eval.load(ROOT/'solver.py')
rows,tasks,couriers=proxy_eval.parse(proxy_eval.DATA.read_text()); keep_t=set(tasks[:30]); keep_c=set(couriers[:60]); out=[]; idx=0
for key,ts,c,sc,w,i in rows:
    if c in keep_c and len(ts)==1 and ts[0] in keep_t:
        out.append((key,ts,c,sc,max(.0001,min(.999,w*.25)),idx)); idx+=1
text=proxy_eval.serialize(out); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
base=mod.solve(text); print('base',round(mod._solution_expected_cost(base,rows,T),6))
by={t:[r for r in rows if r[1][0]==t] for t in T}
for lam in [0,1,2,4,8,12]:
    used=set(); sol=[]; pressure={c:0 for c in couriers}
    # order hard tasks by best pair cost descending so hard tasks choose first
    order=[]
    for t in T:
        cs=sorted(by[t],key=mod._single_expected_cost)[:20]; best=1e9
        for i,a in enumerate(cs):
            for b in cs[i+1:]: best=min(best,mod._group_expected_cost([a,b],1))
        order.append((best,t))
    for _,t in sorted(order, reverse=True):
        cs=[r for r in by[t] if r[2] not in used]
        top=sorted(cs,key=mod._single_expected_cost)[:22]
        best=None
        for i,a in enumerate(top):
            groups=[[a]]
            for b in top[i+1:]: groups.append([a,b])
            for g in groups:
                val=mod._group_expected_cost(g,1)+lam*sum(pressure[x[2]] for x in g)
                if best is None or val<best[0]: best=(val,g)
        if best:
            g=best[1]; sol.append((t,[r[2] for r in g]));
            for r in g: used.add(r[2]); pressure[r[2]]+=1
    print('lam',lam,'cost',round(mod._solution_expected_cost(sol,rows,T),6),'n',len(sol),'sig',hashlib.sha256(str(sol).encode()).hexdigest()[:10])
