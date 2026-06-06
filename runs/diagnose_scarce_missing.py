#!/usr/bin/env python3
import sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
for p in sys.argv[1:] or ['solver.py']:
    mod=proxy_eval.load(ROOT/p)
    text=proxy_eval.make_scarce(); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
    t0=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t0
    lut={(r[0],r[2]):r for r in rows}
    cov=set(); used=set(); details=[]
    for k,cs in out:
        for c in cs:
            r=lut.get((k,c))
            if r:
                cov.update(r[1]); used.add(c); details.append((k,tuple(r[1]),tuple(cs),mod._group_expected_cost([lut[(k,c)] for c in cs if (k,c) in lut],len(r[1])))); break
    miss=sorted(T-cov)
    print(p,'cost',round(mod._solution_expected_cost(out,rows,T),6),'time',round(dt,3),'cov',len(cov),'miss',miss,'n',len(out),'sig',hashlib.sha256(str(out).encode()).hexdigest()[:12])
    print('worst',sorted(details,key=lambda x:x[3], reverse=True)[:8])
    for m in miss:
        opts=[]
        for r in rows:
            if m in r[1] and r[2] not in used:
                opts.append((mod._group_expected_cost([r],len(r[1])),r[0],r[1],r[2],r[3],r[4]))
        print('missing options',m,sorted(opts)[:10])
