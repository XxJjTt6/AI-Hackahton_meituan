#!/usr/bin/env python3
import sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval

def make_low_single_only(scale=.25, nt=30, nc=60):
    rows,tasks,couriers=proxy_eval.parse(proxy_eval.DATA.read_text())
    keep_t=set(tasks[:nt]); keep_c=set(couriers[:nc])
    out=[]; idx=0
    for key,ts,c,sc,w,i in rows:
        if c in keep_c and len(ts)==1 and ts[0] in keep_t:
            out.append((key,ts,c,sc,max(.0001,min(.999,w*scale)),idx)); idx+=1
    return proxy_eval.serialize(out)

def evalp(path):
    mod=proxy_eval.load(ROOT/path)
    text=make_low_single_only(.25); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
    t0=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t0
    sig=hashlib.sha256('\n'.join(f'{k}:{",".join(cs)}' for k,cs in out).encode()).hexdigest()[:12]
    kd={}
    for k,cs in out: kd[len(cs)]=kd.get(len(cs),0)+1
    print(path,'rows',len(rows),'cost',round(mod._solution_expected_cost(out,rows,T),6),'time',round(dt,3),'n',len(out),'k',kd,'sig',sig)
    for k,cs in out[:8]: print(' ',k,cs)
if __name__=='__main__':
    for p in sys.argv[1:] or ['solver.py']: evalp(p)
