#!/usr/bin/env python3
import json, time, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
mod=proxy_eval.load(ROOT/'solver.py')
def sig(out):
    return hashlib.sha256('\n'.join(f'{k}:{",".join(cs)}' for k,cs in out).encode()).hexdigest()
records=[]
for name,text in [('large',proxy_eval.DATA.read_text()),('low020',proxy_eval.make_low(.20)),('low025',proxy_eval.make_low(.25)),('low030',proxy_eval.make_low(.30)),('low035',proxy_eval.make_low(.35)),('scarce40',proxy_eval.make_scarce())]:
    rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
    t0=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t0
    records.append({'case':name,'time':dt,'cost':mod._solution_expected_cost(out,rows,T),'min_score':mod._solution_expected_cost_by_model(out,rows,T,'min_score'),'max_willingness':mod._solution_expected_cost_by_model(out,rows,T,'max_willingness'),'groups':len(out),'kdist':{str(k):sum(1 for _,cs in out if len(cs)==k) for k in sorted({len(cs) for _,cs in out})},'sig':sig(out)})
print(json.dumps(records,ensure_ascii=False,indent=2))
(ROOT/'runs/local_best_signature_f65d16ac.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
