#!/usr/bin/env python3
import sys,time,hashlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
cases=[('large',proxy_eval.DATA.read_text()),('low025',proxy_eval.make_low(.25)),('singlelow',None)]
def make_low_single_only(scale=.25, nt=30, nc=60):
    rows,tasks,couriers=proxy_eval.parse(proxy_eval.DATA.read_text())
    keep_t=set(tasks[:nt]); keep_c=set(couriers[:nc])
    out=[]; idx=0
    for key,ts,c,sc,w,i in rows:
        if c in keep_c and len(ts)==1 and ts[0] in keep_t:
            out.append((key,ts,c,sc,max(.0001,min(.999,w*scale)),idx)); idx+=1
    return proxy_eval.serialize(out)
cases[2]=('singlelow',make_low_single_only(.25))
for p in sys.argv[1:] or ['solver.py']:
    mod=proxy_eval.load(ROOT/p)
    print('##',p,flush=True)
    for name,text in cases:
        rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks); cnt=collections.Counter(); vals=[]
        for i in range(5):
            t0=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t0
            sig=hashlib.sha256('\n'.join(f'{k}:{",".join(cs)}' for k,cs in out).encode()).hexdigest()[:12]
            cost=round(mod._solution_expected_cost(out,rows,T),6); cnt[(sig,cost)]+=1; vals.append(dt)
            print(name,i+1,cost,round(dt,3),sig,flush=True)
        print('summary',name,cnt,'time_range',round(min(vals),3),round(max(vals),3),flush=True)
