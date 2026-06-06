#!/usr/bin/env python3
"""Low multi-task bundle shape master.
For each task_key (including bundles), build best legal courier group columns, then solve set packing.
Different from prior dual probe: keeps multi-task bundle rows and tries broader top pools per key.
"""
import importlib.util, itertools, json, sys, time, hashlib
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
spec=importlib.util.spec_from_file_location('solver',ROOT/'solver.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def popc(x): return bin(x).count('1')
def sig(sol): return hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in sol)).encode()).hexdigest()[:12]

def master(text, seconds=8.8, top=14, per_key=10, max_group=5, max_cols=900):
 rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks); end=time.monotonic()+seconds
 base=m.solve(text); base_cost=m._solution_expected_cost(base,rows,T)
 task_index={t:i for i,t in enumerate(tasks)}; courier_index={c:i for i,c in enumerate(sorted({r[2] for r in rows}))}
 bykey={}
 for r in rows: bykey.setdefault(r[0],[]).append(r)
 cols=[]
 # incumbent columns
 rowmap={(r[0],r[2]):r for r in rows}
 for k,grp in m._result_to_selected(base,rowmap).items():
  tm=sum(1<<task_index[t] for t in grp[0][1]); cm=0
  for r in grp: cm|=1<<courier_index[r[2]]
  cost=m._group_expected_cost(grp,len(grp[0][1])); cols.append((cost-100*len(grp[0][1]),cost,tm,cm,tuple(grp),'inc'))
 for key,rs in bykey.items():
  if time.monotonic()>end-1.0: break
  ts=rs[0][1]; tc=len(ts); tm=sum(1<<task_index[t] for t in ts)
  ranked=[]; seen=set()
  ranklists=[
   sorted(rs,key=lambda r:(m._group_expected_cost([r],tc),-r[4],r[5])),
   sorted(rs,key=lambda r:(r[3],-r[4],r[5])),
   sorted(rs,key=lambda r:(-r[4],r[3],r[5])),
   sorted(rs,key=lambda r:(r[3]*max(.05,r[4]),r[5])),
  ]
  for lst in ranklists:
   for r in lst[:top]:
    if r[2] not in seen: seen.add(r[2]); ranked.append(r)
  local=[]
  maxg=min(max_group,len(ranked))
  # For big bundles, groups of 1-3 often enough; for singles allow more.
  ks=range(1,maxg+1) if tc==1 else range(1,min(maxg,4)+1)
  for k in ks:
   lim=min(len(ranked), top if k<=3 else 10)
   for comb in itertools.combinations(ranked[:lim],k):
    if len({r[2] for r in comb})<k: continue
    cost=m._group_expected_cost(comb,tc); gain=100*tc-cost
    if gain<=1e-9: continue
    cm=0
    for r in comb: cm|=1<<courier_index[r[2]]
    local.append((cost-100*tc,cost,tm,cm,tuple(comb),'gen'))
   if time.monotonic()>end-1.0: break
  local=sorted(local,key=lambda x:(x[0],x[1]))[:per_key]
  cols.extend(local)
 cols=sorted(cols,key=lambda x:(x[0]/max(1,popc(x[2])),x[0],x[1]))[:max_cols]
 full=(1<<len(tasks))-1; bytask=[[] for _ in tasks]
 for col in cols:
  mask=col[2]
  for i in range(len(tasks)):
   if mask>>i&1: bytask[i].append(col)
 # greedy initial
 best=[]; best_red=0; cm=0; tm=0
 for col in cols:
  if col[2]&tm or col[3]&cm: continue
  if col[0]<0:
   best.append(col); tm|=col[2]; cm|=col[3]; best_red+=col[0]
 chosen=[]
 def dfs(mask,cmask,red,depth=0):
  nonlocal best,best_red
  if time.monotonic()>end-.04: return
  # optimistic simple bound from uncovered best negative per task
  if mask==full or depth>len(tasks):
   if red<best_red: best_red=red; best=list(chosen)
   return
  rem=[i for i in range(len(tasks)) if not (mask>>i)&1]
  if not rem:
   if red<best_red: best_red=red; best=list(chosen)
   return
  i=min(rem,key=lambda j:sum(1 for c in bytask[j][:60] if not c[2]&mask and not c[3]&cmask))
  # skip this task
  dfs(mask|1<<i,cmask,red,depth+1)
  for col in bytask[i][:70]:
   if col[2]&mask or col[3]&cmask: continue
   # weak pruning
   if red+col[0] > best_red+50: continue
   chosen.append(col); dfs(mask|col[2],cmask|col[3],red+col[0],depth+1); chosen.pop()
 dfs(0,0,0)
 out=[]
 for col in best:
  grp=sorted(col[4],key=lambda r:(r[3],-r[4],r[5])); out.append((grp[0][0],[r[2] for r in grp]))
 cost=m._solution_expected_cost(out,rows,T)
 return out,cost,{'base_cost':base_cost,'cols':len(cols),'best_red':best_red,'base_sig':sig(base)}

report={}
for case,text in {'official_like':(ROOT/'runs/official_like_low_synth.txt').read_text(),'low025':proxy_eval.make_low(.25),'low030':proxy_eval.make_low(.30),'calibrated':(ROOT/'runs/official_calibrated_low_synth.txt').read_text()}.items():
 for top,per,maxg,maxcols in [(10,6,4,600),(14,10,5,900),(18,12,5,1100)]:
  out,cost,info=master(text,8.8,top,per,maxg,maxcols)
  shape={}
  for k,cs in out: shape[str(len(cs))]=shape.get(str(len(cs)),0)+1
  key=f'top{top}_per{per}_g{maxg}_c{maxcols}'
  report.setdefault(case,{})[key]={'cost':cost,'delta':cost-info['base_cost'],'sig':sig(out),'shape':shape,'rows':len(out),'info':info}
  print(case,key,report[case][key],flush=True)
(ROOT/'runs/night_20260526/round15_low_bundle_shape_master.json').write_text(json.dumps(report,indent=2,sort_keys=True))
