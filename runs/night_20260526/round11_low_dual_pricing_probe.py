#!/usr/bin/env python3
"""Prototype a dual-price style column search for low cases.
Generate many task-key columns with reduced cost against simple task prices,
then solve bounded set packing. Isolated experiment only.
"""
import importlib.util, itertools, json, sys, time, hashlib, math
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
spec=importlib.util.spec_from_file_location('solver',ROOT/'solver.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def solve_pricing(text, seconds=8.5):
 rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks); start=time.monotonic(); end=start+seconds
 base=m.solve(text); base_cost=m._solution_expected_cost(base,rows,T)
 # task price: penalty plus incumbent group average if covered
 prices={t:100.0 for t in T}
 rowmap={(r[0],r[2]):r for r in rows}; sel=m._result_to_selected(base,rowmap)
 for k,grp in sel.items():
  cost=m._group_expected_cost(grp,len(grp[0][1]))/len(grp[0][1])
  for t in grp[0][1]: prices[t]=min(prices[t],cost)
 bykey={}
 for r in rows: bykey.setdefault(r[0],[]).append(r)
 task_index={t:i for i,t in enumerate(sorted(T))}; courier_index={c:i for i,c in enumerate(sorted({r[2] for r in rows}))}
 cols=[]
 for key,rs in bykey.items():
  if time.monotonic()>end-1.0: break
  ts=rs[0][1]; taskmask=sum(1<<task_index[t] for t in ts); price=sum(prices[t] for t in ts)
  # union of rank lists: expected, score, willingness
  pool=[]; seen=set()
  for ranked in [sorted(rs,key=lambda r:(m._group_expected_cost([r],len(ts)),-r[4],r[5])), sorted(rs,key=lambda r:(r[3],-r[4],r[5])), sorted(rs,key=lambda r:(-r[4],r[3],r[5]))]:
   for r in ranked[:16]:
    if r[2] not in seen: seen.add(r[2]); pool.append(r)
  best=[]
  for maxk in (1,2,3,4,5,6):
   lim=10 if maxk<=4 else 8
   for comb in itertools.combinations(pool[:lim],maxk):
    if len({r[2] for r in comb})<len(comb): continue
    cost=m._group_expected_cost(comb,len(ts)); gain=100*len(ts)-cost; red=cost-price
    if gain>1e-9: best.append((red,cost,gain,comb))
   if time.monotonic()>end-1.0: break
  best=sorted(best,key=lambda x:(x[0],x[1]))[:8]
  for red,cost,gain,comb in best:
   cm=0
   for r in comb: cm |= 1<<courier_index[r[2]]
   cols.append((cost-100*len(ts),cost,taskmask,cm,comb))
 # include incumbent groups
 for k,grp in sel.items():
  tm=sum(1<<task_index[t] for t in grp[0][1]); cm=0
  for r in grp: cm|=1<<courier_index[r[2]]
  cost=m._group_expected_cost(grp,len(grp[0][1])); cols.append((cost-100*len(grp[0][1]),cost,tm,cm,tuple(grp)))
 # bounded DFS set packing on most promising columns
 cols=sorted(cols,key=lambda x:(x[0]/max(1,bin(x[2]).count("1")),x[0]))[:600]
 full=(1<<len(T))-1; best_cols=[]; best_red=0; chosen=[]
 bytask=[[] for _ in tasks]
 for c in cols:
  for i in range(len(tasks)):
   if c[2]>>i&1: bytask[i].append(c)
 mins=[min([0]+[c[0] for c in bytask[i]]) for i in range(len(tasks))]
 def lb(mask,red):
  s=red; rem=full&~mask
  while rem:
   bit=rem&-rem; i=bit.bit_length()-1; s+=mins[i]; rem^=bit
  return s
 sys.setrecursionlimit(10000)
 def dfs(mask,cmask,red):
  nonlocal best_red,best_cols
  if time.monotonic()>end-.05: return
  if lb(mask,red)>=best_red-1e-9: return
  if mask==full:
   if red<best_red: best_red=red; best_cols=list(chosen)
   return
  # pick uncovered task with fewest compatible cols
  rem=[i for i in range(len(tasks)) if not (mask>>i)&1]
  i=min(rem,key=lambda j:sum(1 for c in bytask[j] if not c[2]&mask and not c[3]&cmask))
  for c in bytask[i][:80]:
   if c[2]&mask or c[3]&cmask: continue
   chosen.append(c); dfs(mask|c[2],cmask|c[3],red+c[0]); chosen.pop()
  dfs(mask| (1<<i), cmask, red) # leave unassigned, red 0 relative to penalty
 dfs(0,0,0)
 if not best_cols: return base,base_cost,{'cols':len(cols),'best_red':best_red,'base_cost':base_cost}
 out=[]
 for c in best_cols:
  grp=sorted(c[4],key=lambda r:(r[3],-r[4],r[5])); out.append((grp[0][0],[r[2] for r in grp]))
 cost=m._solution_expected_cost(out,rows,T)
 return out,cost,{'cols':len(cols),'best_red':best_red,'base_cost':base_cost}

def sig(out): return hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in out)).encode()).hexdigest()[:12]
report={}
for name,text in {'official_like':(ROOT/'runs/official_like_low_synth.txt').read_text(),'low025':proxy_eval.make_low(.25),'low030':proxy_eval.make_low(.30)}.items():
 out,cost,info=solve_pricing(text,8.7)
 shape={}
 for k,cs in out: shape[str(len(cs))]=shape.get(str(len(cs)),0)+1
 report[name]={'cost':cost,'sig':sig(out),'shape':shape,'info':info}
 print(name,report[name],flush=True)
(ROOT/'runs/night_20260526/round11_low_dual_pricing_probe.json').write_text(json.dumps(report,indent=2,sort_keys=True))
