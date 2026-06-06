#!/usr/bin/env python3
"""Legal ejection-chain probe for scarce-like cases.
Try to cover one missing task by replacing/evicting up to 3 existing groups while preserving unique couriers.
Isolated experiment only.
"""
import importlib.util, json, sys, time, itertools, hashlib
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
spec=importlib.util.spec_from_file_location('solver',ROOT/'solver.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def sig(sol): return hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in sol)).encode()).hexdigest()[:12]

def repair(result, rows, tasks, seconds=2.5):
 end=time.monotonic()+seconds; rowmap={(r[0],r[2]):r for r in rows}; selected=m._result_to_selected(result,rowmap)
 best=result; best_cost=m._solution_expected_cost(best,rows,tasks)
 bytask={}
 for r in rows:
  for t in r[1]: bytask.setdefault(t,[]).append(r)
 def format_sel(sel): return m._format_selected(sel)
 while time.monotonic()<end-.05:
  covered={t for grp in selected.values() for t in grp[0][1]}
  missing=sorted(set(tasks)-covered)
  if not missing: break
  improved=False
  for miss in missing:
   candidates=[]
   for r in sorted(bytask.get(miss,[]), key=lambda r:(m._group_expected_cost([r],len(r[1])),-r[4],r[5]))[:60]:
    needed=set(r[1]); courier=r[2]
    conflict_keys={k for k,g in selected.items() if set(g[0][1]) & needed or any(x[2]==courier for x in g)}
    # also try combining with one existing missing-related row group replacement by _repair_task_window
    for extra in range(0,3):
     keys=list(conflict_keys)
     # add worst groups to free couriers/tasks
     groups=sorted(m._selected_repair_groups(selected), reverse=True)
     for g in groups[:extra]:
      if g[2] not in keys: keys.append(g[2])
     win=set(needed)
     for k in keys:
      if k in selected: win.update(selected[k][0][1])
     if len(win)>14: continue
     newsel=dict(selected)
     for k in keys: newsel.pop(k,None)
     used_c={x[2] for grp in newsel.values() for x in grp}
     if courier in used_c: continue
     # solve local window legally with existing repair primitive from current partial selected
     cand=m._repair_task_window(newsel, rows, tasks, win, min(end,time.monotonic()+.18), top_riders_per_task_key=10, max_k=4, option_limit=80)
     if not cand: continue
     cost=m._solution_expected_cost(cand,rows,tasks)
     if cost<best_cost-1e-9 and m._solution_covered_count(cand,rows)>=m._solution_covered_count(best,rows):
      best=cand; best_cost=cost; selected=m._result_to_selected(best,rowmap); improved=True; break
    if improved or time.monotonic()>end-.05: break
   if improved or time.monotonic()>end-.05: break
  if not improved: break
 return best,best_cost

def run_case(name,text):
 rows,tasks,c=proxy_eval.parse(text); T=set(tasks); base=m.solve(text); base_cost=m._solution_expected_cost(base,rows,T)
 best,cost=repair(base,rows,T,3.0)
 return {'base':base_cost,'after':cost,'delta':cost-base_cost,'base_cov':m._solution_covered_count(base,rows),'after_cov':m._solution_covered_count(best,rows),'base_sig':sig(base),'after_sig':sig(best),'rows':len(best)}
texts={'scarce40':proxy_eval.make_scarce(),'large':proxy_eval.DATA.read_text(),'official_like':(ROOT/'runs/official_like_low_synth.txt').read_text(),'low025':proxy_eval.make_low(.25)}
report={}
for name,text in texts.items():
 report[name]=run_case(name,text); print(name,report[name],flush=True)
(ROOT/'runs/night_20260526/round12_legal_ejection_chain_probe.json').write_text(json.dumps(report,indent=2,sort_keys=True))
