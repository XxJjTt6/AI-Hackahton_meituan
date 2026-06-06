#!/usr/bin/env python3
"""Exact-ish assignment for low case restricted to single-task rows with up to K riders per task.
This tests whether current mixed bundles are actually worse than a globally optimized single-task multi-dispatch.
"""
import importlib.util, json, sys, time, itertools, hashlib
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
spec=importlib.util.spec_from_file_location('solver',ROOT/'solver.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def solve_single_exact(text, top=12, maxk=4, seconds=8.5):
 rows,tasks,c=proxy_eval.parse(text); T=set(tasks); end=time.monotonic()+seconds
 singles=[r for r in rows if len(r[1])==1]
 task_index={t:i for i,t in enumerate(tasks)}; courier_index={cc:i for i,cc in enumerate(sorted({r[2] for r in rows}))}
 cols=[]
 bytask={}
 for r in singles: bytask.setdefault(r[1][0],[]).append(r)
 for t,rs in bytask.items():
  rs=sorted(rs,key=lambda r:(m._group_expected_cost([r],1),r[3],-r[4],r[5]))[:top]
  for k in range(1,min(maxk,len(rs))+1):
   for comb in itertools.combinations(rs,k):
    cm=0
    for r in comb: cm |= 1<<courier_index[r[2]]
    cost=m._group_expected_cost(comb,1); red=cost-100
    if red<0: cols.append((red,cost,1<<task_index[t],cm,comb))
  if time.monotonic()>end-1: break
 cols=sorted(cols,key=lambda x:(x[0],x[1]))
 by_t=[[] for _ in tasks]
 for col in cols:
  i=(col[2]).bit_length()-1; by_t[i].append(col)
 best=[]; best_red=0; chosen=[]; full=(1<<len(tasks))-1
 def dfs(i,cm,red):
  nonlocal best,best_red
  if time.monotonic()>end-.05: return
  if i>=len(tasks):
   if red<best_red: best_red=red; best=list(chosen)
   return
  # skip task penalty (red 0)
  dfs(i+1,cm,red)
  for col in by_t[i][:80]:
   if col[3]&cm: continue
   chosen.append(col); dfs(i+1,cm|col[3],red+col[0]); chosen.pop()
 dfs(0,0,0)
 out=[]
 for col in best:
  grp=sorted(col[4],key=lambda r:(r[3],-r[4],r[5])); out.append((grp[0][0],[r[2] for r in grp]))
 return out, rows, T, {'cols':len(cols),'best_red':best_red}

def sig(out): return hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in out)).encode()).hexdigest()[:12]
report={}
for case,text in {'official_like':(ROOT/'runs/official_like_low_synth.txt').read_text(),'low025':proxy_eval.make_low(.25),'low030':proxy_eval.make_low(.30),'calibrated':(ROOT/'runs/official_calibrated_low_synth.txt').read_text()}.items():
 base_mod=m.solve(text); rows,tasks,c=proxy_eval.parse(text); T=set(tasks); base=m._solution_expected_cost(base_mod,rows,T)
 for top,maxk in [(8,3),(12,4),(16,5)]:
  out,rr,TT,info=solve_single_exact(text,top,maxk,8.7)
  cost=m._solution_expected_cost(out,rr,TT); key=f'top{top}_k{maxk}'
  report.setdefault(case,{})[key]={'cost':cost,'base':base,'delta':cost-base,'cov':m._solution_covered_count(out,rr),'rows':len(out),'sig':sig(out),'info':info}
  print(case,key,report[case][key],flush=True)
(ROOT/'runs/night_20260526/round14_low_single_multirider_exact.json').write_text(json.dumps(report,indent=2,sort_keys=True))
