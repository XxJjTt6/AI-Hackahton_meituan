#!/usr/bin/env python3
import sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
for arg in sys.argv[1:] or ['solver.py']:
    mod=proxy_eval.load(ROOT/arg)
    print('solver',arg, flush=True)
    for name,text in [('low020',proxy_eval.make_low(.20)),('low025',proxy_eval.make_low(.25)),('low030',proxy_eval.make_low(.30)),('low035',proxy_eval.make_low(.35))]:
        rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
        t0=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t0
        kd={}
        for k,cs in out: kd[len(cs)]=kd.get(len(cs),0)+1
        print(name, 'time', round(dt,2), 'cost', round(mod._solution_expected_cost(out,rows,T),2), 'min', round(mod._solution_expected_cost_by_model(out,rows,T,'min_score'),2), 'will', round(mod._solution_expected_cost_by_model(out,rows,T,'max_willingness'),2), 'k', kd, flush=True)
