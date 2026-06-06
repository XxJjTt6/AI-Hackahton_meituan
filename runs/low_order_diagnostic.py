#!/usr/bin/env python3
import sys,random,hashlib
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
def greedy(order):
    used=set(); sol=[]
    for t in order:
        best=None
        avail=[r for r in by[t] if r[2] not in used]
        for i in range(len(avail)):
            # try k1,k2,k3 small top by single cost
            pass
        top=sorted(avail,key=lambda r:mod._single_expected_cost(r))[:18]
        groups=[]
        for i,a in enumerate(top):
            groups.append((mod._group_expected_cost([a],1),[a]))
            for j,b in enumerate(top[i+1:],i+1):
                groups.append((mod._group_expected_cost([a,b],1),[a,b]))
                for c in top[j+1:j+5]: groups.append((mod._group_expected_cost([a,b,c],1),[a,b,c]))
        if not groups: continue
        cost,g=min(groups,key=lambda x:x[0]); sol.append((t,[r[2] for r in g])); used.update(r[2] for r in g)
    return sol
orders=[sorted(T), sorted(T, reverse=True)]
for seed in range(12):
    o=sorted(T); random.Random(seed).shuffle(o); orders.append(o)
best=(1e9,None)
for i,o in enumerate(orders):
    sol=greedy(o); cost=mod._solution_expected_cost(sol,rows,T)
    if cost<best[0]: best=(cost,sol)
    print(i,round(cost,6),len(sol),hashlib.sha256(str(sol).encode()).hexdigest()[:10])
print('best',round(best[0],6),best[1][:5])
