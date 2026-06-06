#!/usr/bin/env python3
import sys,time,itertools,heapq
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval, solver

def solve_proto(text, deadline):
    rows,tasks,couriers=proxy_eval.parse(text); tasks=sorted(tasks); tid={t:i for i,t in enumerate(tasks)}; cid={c:i for i,c in enumerate(couriers)}
    bykey={}
    for r in rows: bykey.setdefault(r[0],[]).append(r)
    cols=[]
    for key,rs in bykey.items():
        if len(cols)>5000 and time.monotonic()>deadline-.5: break
        ts=tuple(x.strip() for x in key.split(',') if x.strip())
        if len(ts)>2: continue
        rs=sorted(rs,key=lambda r: solver._group_expected_cost([r],len(ts)))[:14]
        tm=0
        for t in ts: tm|=1<<tid[t]
        for k in range(1,min(5,len(rs))+1):
            for comb in itertools.combinations(rs,k):
                cm=0; ok=True
                for r in comb:
                    bit=1<<cid[r[2]]
                    if cm&bit: ok=False; break
                    cm|=bit
                if not ok: continue
                cost=solver._group_expected_cost(comb,len(ts)); gain=100*len(ts)-cost
                if gain>1e-9: cols.append((gain,cost,tm,cm,key,tuple(r[2] for r in sorted(comb,key=lambda r:(r[3],-r[4],r[5])))))
    cols=sorted(cols,reverse=True)[:900]
    states={(0,0):(0,())}
    for i,col in enumerate(cols):
        if time.monotonic()>deadline-.05: break
        gain,cost,tm,cm,key,cs=col; add=[]
        for (tmask,cmask),(val,chosen) in list(states.items()):
            if tmask&tm or cmask&cm: continue
            nk=(tmask|tm,cmask|cm); nv=val+gain
            old=states.get(nk)
            if old is None or nv>old[0]: add.append((nk,(nv,chosen+(i,))))
        for nk,v in add: states[nk]=v
        if len(states)>5000:
            states=dict(sorted(states.items(),key=lambda kv:(bin(kv[0][0]).count('1'),kv[1][0]), reverse=True)[:2000])
    best=max(states.items(),key=lambda kv:(bin(kv[0][0]).count('1'),kv[1][0]))[1][1]
    out=[(cols[i][4],list(cols[i][5])) for i in best]
    return out, rows, set(tasks)

for scale in [.2,.25,.3,.35]:
    text=proxy_eval.make_low(scale)
    mod=solver
    base=mod.solve(text); rows,tasks,c=proxy_eval.parse(text); T=set(tasks)
    proto,rows2,T2=solve_proto(text,time.monotonic()+4.0)
    print('scale',scale,'base',round(mod._solution_expected_cost(base,rows,T),2),'proto',round(mod._solution_expected_cost(proto,rows,T),2),'groups',len(proto),'cov',solver._solution_covered_count(proto,rows))
