#!/usr/bin/env python3
import sys,time,hashlib
from pathlib import Path
sys.path.insert(0,'runs')
import proxy_eval
for path in sys.argv[1:] or ['solver.py']:
    mod=proxy_eval.load(path); text=proxy_eval.DATA.read_text(); rows,tasks,couriers=proxy_eval.parse(text)
    for i in range(3):
        t=time.monotonic(); res=mod.solve(text); dt=time.monotonic()-t
        print(path,'trial',i,'time',round(dt,3),'cost',round(mod._solution_expected_cost(res,rows,set(tasks)),6),'sig',hashlib.sha256(str(res).encode()).hexdigest()[:10],flush=True)
