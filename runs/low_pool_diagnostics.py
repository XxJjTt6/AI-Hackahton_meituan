#!/usr/bin/env python3
import sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval, solver
for scale in [.2,.25,.3,.35]:
    rows,tasks,couriers=proxy_eval.parse(proxy_eval.make_low(scale)); T=set(tasks)
    singles=[r for r in rows if len(r[1])==1]
    # per-task best k=1, k=2 exact among top 20 singles by cost
    total1=total2=0; total3=0
    for t in tasks:
        rs=sorted([r for r in singles if r[1][0]==t], key=lambda r: solver._single_expected_cost(r))[:20]
        best1=min((solver._group_expected_cost([a],1) for a in rs), default=100)
        best2=best1; best3=best1
        for i,a in enumerate(rs):
            for b in rs[i+1:]:
                best2=min(best2, solver._group_expected_cost([a,b],1))
                for c in rs[i+2:i+8]:
                    if c[2] not in (a[2],b[2]): best3=min(best3, solver._group_expected_cost([a,b,c],1))
        total1+=best1; total2+=best2; total3+=best3
    print('scale',scale,'independent best k1',round(total1,2),'k2',round(total2,2),'k3local',round(total3,2),'couriers',len(couriers))
