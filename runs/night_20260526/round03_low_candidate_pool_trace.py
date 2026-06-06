#!/usr/bin/env python3
import importlib.util, json, sys, time, hashlib
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
SOLVER=ROOT/'solver.py'
CASES={'official_like':(ROOT/'runs/official_like_low_synth.txt').read_text(),'calibrated':(ROOT/'runs/official_calibrated_low_synth.txt').read_text(),'low025':proxy_eval.make_low(.25),'low030':proxy_eval.make_low(.30)}
spec=importlib.util.spec_from_file_location('solver_trace',SOLVER); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
orig=m._pick_low_robust_best
report={}

def sig(sol): return hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in sol)).encode()).hexdigest()[:12]
def shape(sol):
 d={}
 for k,cs in sol: d[str(len(cs))]=d.get(str(len(cs)),0)+1
 return d
for name,text in CASES.items():
 rows,tasks,c=proxy_eval.parse(text); T=set(tasks); logs=[]
 def picker(solutions,candidates,all_tasks):
  entries=[]
  for idx,s in enumerate([x for x in solutions if x]):
   entries.append({'idx':idx,'cost':m._solution_expected_cost(s,candidates,all_tasks),'min':m._solution_expected_cost_by_model(s,candidates,all_tasks,'min_score'),'maxw':m._solution_expected_cost_by_model(s,candidates,all_tasks,'max_willingness'),'cov':m._solution_covered_count(s,candidates),'rows':len(s),'shape':shape(s),'sig':sig(s)})
  entries.sort(key=lambda x:x['cost'])
  chosen=orig(solutions,candidates,all_tasks)
  logs.append({'n':len(entries),'top_by_cost':entries[:20],'chosen':{'cost':m._solution_expected_cost(chosen,candidates,all_tasks),'sig':sig(chosen),'shape':shape(chosen)}})
  return chosen
 m._pick_low_robust_best=picker
 t=time.monotonic(); out=m.solve(text); dt=time.monotonic()-t
 report[name]={'elapsed':dt,'final':{'cost':m._solution_expected_cost(out,rows,T),'min':m._solution_expected_cost_by_model(out,rows,T,'min_score'),'maxw':m._solution_expected_cost_by_model(out,rows,T,'max_willingness'),'sig':sig(out),'shape':shape(out)},'pick_calls':logs}
 print(name, report[name]['final'], 'elapsed', dt, 'calls', len(logs), flush=True)
 m._pick_low_robust_best=orig
(ROOT/'runs/night_20260526/round03_low_candidate_pool_trace.json').write_text(json.dumps(report,indent=2,sort_keys=True))
