#!/usr/bin/env python3
import importlib.util, json, hashlib, sys, time, statistics
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
spec=importlib.util.spec_from_file_location('solver',ROOT/'solver.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
cases={'official_like':(ROOT/'runs/official_like_low_synth.txt').read_text(),'low025':proxy_eval.make_low(.25),'low030':proxy_eval.make_low(.30)}
report={}
for name,text in cases.items():
 rows,tasks,c=proxy_eval.parse(text); T=set(tasks); rec=[]
 for i in range(20):
  t=time.monotonic(); out=m.solve(text); dt=time.monotonic()-t
  sig=hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in out)).encode()).hexdigest()[:12]
  shape={}
  for k,cs in out: shape[str(len(cs))]=shape.get(str(len(cs)),0)+1
  rec.append({'cost':m._solution_expected_cost(out,rows,T),'time':dt,'sig':sig,'shape':shape})
  print(name,i,rec[-1],flush=True)
 costs=[r['cost'] for r in rec]
 report[name]={'runs':rec,'mean':statistics.mean(costs),'best':min(costs),'worst':max(costs),'sigs':sorted({r['sig'] for r in rec})}
(ROOT/'runs/night_20260526/round10_low_best_of_many_jitter.json').write_text(json.dumps(report,indent=2,sort_keys=True))
