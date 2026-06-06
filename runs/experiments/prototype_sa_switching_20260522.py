#!/usr/bin/env python3
import importlib.util,pathlib,time,random,sys,math
ROOT=pathlib.Path(__file__).resolve().parents[2]
SOLVER=ROOT/'runs/baselines/official_best_7046558e_robust_cache.py'
spec=importlib.util.spec_from_file_location('s',SOLVER); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse(text):
 rows=[]; tasks=set(); lines=text.strip().splitlines(); st=1 if lines and lines[0].startswith('task') else 0
 for i,l in enumerate(lines[st:]):
  p=l.split('\t'); ts=tuple(x.strip() for x in p[0].split(',') if x.strip()); r=(p[0],ts,p[1],float(p[2]),float(p[3]),i); rows.append(r); tasks.update(ts)
 return rows,tasks

def run(path, seconds=90):
 text=pathlib.Path(path).read_text(); C,T=parse(text); cur=s.solve(text); best=cur; cc=s._solution_expected_cost(cur,C,T); bc=cc
 lut={(r[0],r[2]):r for r in C}; adj=s._task_adjacency(C); rng=random.Random(220522)
 dead=time.monotonic()+seconds; it=0; selected=s._result_to_selected(cur,lut)
 print('start',pathlib.Path(path).name,cc,'groups',len(cur), flush=True)
 while time.monotonic()<dead:
  it+=1
  sel=s._result_to_selected(cur,lut); groups=s._selected_repair_groups(sel)
  if not groups: break
  groups=sorted(groups,reverse=True)
  mode=it%5
  if mode==0:
   win=s._ranked_repair_window(groups[rng.randrange(min(10,len(groups))):], rng.choice([8,10,12,14,16]))
  elif mode in (1,2):
   g=groups[rng.randrange(min(12,len(groups)))]; win=s._related_repair_window(g[3],sel,adj,rng.choice([8,10,12,14,16]))
  else:
   g=groups[rng.randrange(min(12,len(groups)))]; win=s._random_repair_window(g[3],sel,adj,rng.choice([8,10,12,14,16]),rng)
  cand=s._repair_task_window(sel,C,T,win,min(dead,time.monotonic()+.25),top_riders_per_task_key=16,max_k=5,option_limit=160)
  if not cand: continue
  if time.monotonic()<dead-.05: cand=s._reassign_mixed_solution(cand,C,T,min(dead,time.monotonic()+.08))
  nc=s._solution_expected_cost(cand,C,T)
  temp=max(.05, 3.0*(1-(seconds-(dead-time.monotonic()))/seconds))
  if nc<cc or rng.random()<math.exp((cc-nc)/temp):
   cur=cand; cc=nc
  if nc<bc-1e-9:
   best=cand; bc=nc; print('improve',bc,'delta',bc-s._solution_expected_cost(s.solve(text),C,T),'iter',it,'tleft',dead-time.monotonic(), flush=True)
 print('final',bc,'delta',bc-s._solution_expected_cost(s.solve(text),C,T),'iters',it,'groups',len(best), flush=True)
 if bc < s._solution_expected_cost(s.solve(text),C,T)-1e-9: print(best)
if __name__=='__main__':
 for p in sys.argv[1:]: run(p)
