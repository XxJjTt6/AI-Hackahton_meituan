#!/usr/bin/env python3
# Try random windows of selected low groups and repair them; report best local gain.
import sys,time,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'runs'))
import solver, proxy_eval

def run(scale):
 text=proxy_eval.make_low(scale); rows,tasks,c=proxy_eval.parse(text); T=set(tasks); out=solver.solve(text); base=solver._solution_expected_cost(out,rows,T); best=base
 lut={(r[0],r[2]):r for r in rows}; sel=solver._result_to_selected(out,lut); groups=list(sel.values())
 rng=random.Random(1234)
 for it in range(50):
  keys=[g[0][0] for g in rng.sample(groups,min(4,len(groups)))]
  win=set()
  for k in keys:
   for t in k.split(','): win.add(t)
  cand=solver._repair_task_window(sel,rows,T,win,time.monotonic()+0.12,top_riders_per_task_key=14,max_k=4,option_limit=120)
  if cand:
   cost=solver._solution_expected_cost(cand,rows,T)
   if cost<best: best=cost
 return base,best
for s in [.2,.25,.3,.35]: print(s,run(s))
