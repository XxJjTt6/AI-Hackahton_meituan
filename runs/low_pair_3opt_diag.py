#!/usr/bin/env python3
import sys,itertools,hashlib
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
res=mod.solve(text); sel=mod._result_to_selected(res,row)
items=sorted([(mod._group_expected_cost(g,1),k,g) for k,g in sel.items()], reverse=True)[:8]
print('worst',[ (k,round(c,3),[r[2] for r in g]) for c,k,g in items])
best=(0,None)
for trio in itertools.combinations(items,3):
    keys=[x[1] for x in trio]; groups=[x[2] for x in trio]; sizes=[len(g) for g in groups]
    if sum(sizes)>8: continue
    cour=[r[2] for g in groups for r in g]; old=sum(mod._group_expected_cost(g,1) for g in groups)
    # enumerate assignment of couriers to slots by combinations for first two groups
    for sa in itertools.combinations(cour,sizes[0]):
        rem=[c for c in cour if c not in sa]
        for sb in itertools.combinations(rem,sizes[1]):
            sc=[c for c in rem if c not in sb]
            parts=[sa,sb,sc]; ok=True; new=0
            for k,part in zip(keys,parts):
                rs=[row.get((k,c)) for c in part]
                if any(x is None for x in rs): ok=False; break
                new+=mod._group_expected_cost(rs,1)
            if ok and old-new>best[0]+1e-9: best=(old-new,(keys,parts,old,new))
print('best_gain',best)
