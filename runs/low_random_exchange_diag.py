#!/usr/bin/env python3
import sys,random,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
mod=proxy_eval.load(ROOT/'solver.py')
rows,tasks,couriers=proxy_eval.parse(proxy_eval.DATA.read_text()); keep_t=set(tasks[:30]); keep_c=set(couriers[:60]); out=[]; idx=0
for key,ts,c,sc,w,i in rows:
    if c in keep_c and len(ts)==1 and ts[0] in keep_t: out.append((key,ts,c,sc,max(.0001,min(.999,w*.25)),idx)); idx+=1
text=proxy_eval.serialize(out); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks); row={(r[0],r[2]):r for r in rows}
res=mod.solve(text); sel=mod._result_to_selected(res,row); best=mod._selected_cost(sel,T); rng=random.Random(9)
print('base',round(best,6))
keys=list(sel); deadline=time.monotonic()+4
for it in range(2000):
    if time.monotonic()>deadline: break
    m=rng.randint(4,7); ks=rng.sample(keys,m); cs=[r[2] for k in ks for r in sel[k]]; sizes=[len(sel[k]) for k in ks]
    if len(cs)>12: continue
    # random repartitions preserving sizes
    cur=sum(mod._group_expected_cost(sel[k],1) for k in ks)
    for _ in range(20):
        rng.shuffle(cs); pos=0; newsel={}; ok=True; newcost=0
        for k,sz in zip(ks,sizes):
            part=cs[pos:pos+sz]; pos+=sz; rs=[]
            for c in part:
                r=row.get((k,c))
                if r is None: ok=False; break
                rs.append(r)
            if not ok: break
            newsel[k]=rs; newcost+=mod._group_expected_cost(rs,1)
        if ok and newcost<cur-1e-9:
            for k,rs in newsel.items(): sel[k]=rs
            val=mod._selected_cost(sel,T)
            if val<best-1e-9:
                best=val; print('improve',it,round(best,6),flush=True)
            break
print('final',round(best,6),hashlib.sha256(str(mod._format_selected(sel)).encode()).hexdigest()[:10])
