#!/usr/bin/env python3
import importlib.util, json, sys, time, hashlib
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
# load canonical evaluator
spec=importlib.util.spec_from_file_location('canon', ROOT/'solver.py'); canon=importlib.util.module_from_spec(spec); spec.loader.exec_module(canon)
spec=importlib.util.spec_from_file_location('reuse', ROOT/'runs/solver_reuse_unlimited_refactor_20260523.py'); reuse=importlib.util.module_from_spec(spec); spec.loader.exec_module(reuse)
texts={'official_like':(ROOT/'runs/official_like_low_synth.txt').read_text(),'calibrated':(ROOT/'runs/official_calibrated_low_synth.txt').read_text(),'large':proxy_eval.DATA.read_text(),'scarce40':proxy_eval.make_scarce(),'low025':proxy_eval.make_low(.25),'low030':proxy_eval.make_low(.30)}
report={}
for name,text in texts.items():
 rows,tasks,c=proxy_eval.parse(text); T=set(tasks); rowmap={(r[0],r[2]):r for r in rows}
 t=time.monotonic(); out=reuse.solve(text); dt=time.monotonic()-t
 used_c=[]; used_t=[]; bad=[]
 for k,cs in out:
  if not cs: bad.append(('empty',k)); continue
  group=[]
  for courier in cs:
   r=rowmap.get((k,courier))
   if r is None: bad.append(('missing_row',k,courier)); continue
   group.append(r); used_c.append(courier)
  if group:
   for task in group[0][1]: used_t.append(task)
 canonical_cost=canon._solution_expected_cost(out,rows,T)
 report[name]={'elapsed':dt,'rows':len(out),'canonical_cost':canonical_cost,'reuse_cost':reuse._solution_expected_cost(out,rows,T) if hasattr(reuse,'_solution_expected_cost') else None,'covered_unique':len(set(used_t)),'total_tasks':len(T),'duplicate_couriers':len(used_c)-len(set(used_c)),'duplicate_tasks':len(used_t)-len(set(used_t)),'bad':bad[:20],'sig':hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in out)).encode()).hexdigest()[:12],'sample':out[:8]}
 print(name, report[name], flush=True)
(ROOT/'runs/night_20260526/round07_validate_reuse_refactor.json').write_text(json.dumps(report,indent=2,sort_keys=True))
