#!/usr/bin/env python3
import sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
for p in sys.argv[1:]:
    mod=proxy_eval.load(ROOT/p)
    for name,text in [('low025',proxy_eval.make_low(.25)),('large',proxy_eval.DATA.read_text())]:
        rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
        t0=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t0
        sig=hashlib.sha256('\n'.join(f'{k}:{",".join(cs)}' for k,cs in out).encode()).hexdigest()[:12]
        print(p,name,'cost',round(mod._solution_expected_cost(out,rows,T),6),'time',round(dt,3),'n',len(out),'sig',sig, flush=True)
