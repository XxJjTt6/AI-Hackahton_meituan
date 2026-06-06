#!/usr/bin/env python3
import sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
# make single low
rows,tasks,couriers=proxy_eval.parse(proxy_eval.DATA.read_text()); keep_t=set(tasks[:30]); keep_c=set(couriers[:60]); out=[]; idx=0
for key,ts,c,sc,w,i in rows:
    if c in keep_c and len(ts)==1 and ts[0] in keep_t:
        out.append((key,ts,c,sc,max(.0001,min(.999,w*.25)),idx)); idx+=1
text=proxy_eval.serialize(out); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
mod=proxy_eval.load(ROOT/'solver.py')
res=mod.solve(text); sel=mod._result_to_selected(res,{(r[0],r[2]):r for r in rows})
print('total',mod._solution_expected_cost(res,rows,T))
used={r[2] for g in sel.values() for r in g}
for t,g in sorted(sel.items()):
    k=len(g); cost=mod._group_expected_cost(g,1)
    if k!=2:
        print('\nANOM',t,'k',k,'cost',cost,'couriers',[r[2] for r in g])
        opts=[]
        cand=[r for r in rows if r[1][0]==t]
        for i in range(len(cand)):
            for j in range(i+1,len(cand)):
                if cand[i][2]==cand[j][2]: continue
                # allow all couriers for diagnostic
                opts.append((mod._group_expected_cost([cand[i],cand[j]],1),cand[i][2],cand[j][2],cand[i][3],cand[j][3],cand[i][4],cand[j][4]))
        for o in sorted(opts)[:10]: print(' pair',o)
