#!/usr/bin/env python3
import importlib.util, json, random, sys, time, hashlib, math
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
spec=importlib.util.spec_from_file_location('solver_mod', ROOT/'solver.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def sig(sol): return hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in sol)).encode()).hexdigest()[:12]
def shape(sol):
 d={}
 for k,cs in sol: d[str(len(cs))]=d.get(str(len(cs)),0)+1
 return d

def sa_lns(start,candidates,tasks,seconds,seed=1):
 row_map={(r[0],r[2]):r for r in candidates}
 cur=start; cur_cost=m._solution_expected_cost(cur,candidates,tasks)
 best=cur; best_cost=cur_cost
 selected=m._result_to_selected(cur,row_map)
 groups=m._selected_repair_groups(selected)
 adj=m._task_adjacency(candidates)
 rng=random.Random(seed)
 t0=time.monotonic(); end=t0+seconds; it=0; acc=0; imp=0
 while time.monotonic()<end-.05:
  sel=m._result_to_selected(cur,row_map)
  groups=sorted(m._selected_repair_groups(sel), reverse=True)
  if not groups: break
  mode=it%7
  size=(8,10,12,14,16,18)[it%6]
  if mode==0:
   off=rng.randrange(min(len(groups),12)); win=m._ranked_repair_window(groups[off:],size)
  elif mode in (1,2):
   g=groups[rng.randrange(min(len(groups),18))]; win=m._related_repair_window(g[3],sel,adj,size)
  elif mode in (3,4):
   g=groups[rng.randrange(min(len(groups),18))]; win=m._random_repair_window(g[3],sel,adj,size,rng)
  elif mode==5:
   # union worst with one random related group
   base=set(groups[0][3]); g=groups[rng.randrange(min(len(groups),18))]; win=(base|set(g[3]))
   if len(win)>size: win=set(sorted(win)[:size])
  else:
   uncovered=set(tasks)-{x for rows in sel.values() for x in rows[0][1]}
   if uncovered:
    x=rng.choice(sorted(uncovered)); win=m._uncovered_repair_window(x,sel,adj,size)
   else:
    g=groups[rng.randrange(min(len(groups),18))]; win=set(g[3])
  if not win:
   it+=1; continue
  cand=m._repair_task_window(sel,candidates,tasks,win,min(end,time.monotonic()+.18),top_riders_per_task_key=14,max_k=5,option_limit=120)
  if not cand:
   it+=1; continue
  if time.monotonic()<end-.04:
   cand=m._reassign_mixed_solution(cand,candidates,tasks,min(end,time.monotonic()+.06))
  cc=m._solution_expected_cost(cand,candidates,tasks)
  temp=max(.2, 8.0*(1-(time.monotonic()-t0)/max(.001,seconds)))
  if cc<cur_cost-1e-9 or rng.random()<math.exp(min(0,(cur_cost-cc)/temp)):
   cur=cand; cur_cost=cc; acc+=1
  if cc<best_cost-1e-9:
   best=cand; best_cost=cc; imp+=1
  it+=1
 return best, {'start':m._solution_expected_cost(start,candidates,tasks),'best':best_cost,'sig':sig(best),'shape':shape(best),'iters':it,'accepted':acc,'improvements':imp}

cases={'official_like':(ROOT/'runs/official_like_low_synth.txt').read_text(),'low025':proxy_eval.make_low(.25),'low030':proxy_eval.make_low(.30),'calibrated':(ROOT/'runs/official_calibrated_low_synth.txt').read_text()}
report={}
for name,text in cases.items():
 rows,tasks,c=proxy_eval.parse(text); T=set(tasks)
 base=m.solve(text)
 rec=[]
 for seed in range(5):
  best,info=sa_lns(base,rows,T,seconds=2.8,seed=20260526+seed)
  rec.append(info)
  print(name, seed, info, flush=True)
 report[name]={'base':{'cost':m._solution_expected_cost(base,rows,T),'sig':sig(base),'shape':shape(base)},'runs':rec}
(ROOT/'runs/night_20260526/round05_low_sa_lns_prototype.json').write_text(json.dumps(report,indent=2,sort_keys=True))
