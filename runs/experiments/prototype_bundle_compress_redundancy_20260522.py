#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,pathlib,itertools,time,sys,json,collections
ROOT=pathlib.Path(__file__).resolve().parents[2]
SOLVER=ROOT/'runs/baselines/official_best_7046558e_robust_cache.py'
spec=importlib.util.spec_from_file_location('s',SOLVER); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse(text):
 rows=[]; T=set(); lines=text.strip().splitlines(); st=1 if lines and lines[0].startswith('task') else 0
 for i,l in enumerate(lines[st:]):
  p=l.split('\t'); ts=tuple(x.strip() for x in p[0].split(',') if x.strip()); rows.append((p[0],ts,p[1],float(p[2]),float(p[3]),i)); T.update(ts)
 return rows,T

def selected(sol,C):
 lut={(r[0],r[2]):r for r in C}; d={}
 for k,cs in sol:
  rr=[lut.get((k,c)) for c in cs]; rr=[r for r in rr if r]
  if rr: d[k]=rr
 return d

def add_best_redundancy(sel,C,T,free,deadline):
 # greedily insert free couriers into existing compatible groups by exact marginal gain
 by_c=collections.defaultdict(list)
 for r in C: by_c[r[2]].append(r)
 free=set(free); sel={k:list(v) for k,v in sel.items()}
 while free and time.monotonic()<deadline-.02:
  best=None; best_delta=0.0
  for c in list(free):
   for r in by_c.get(c,[]):
    k=r[0]
    if k not in sel: continue
    group=sel[k]
    if any(x[2]==c for x in group): continue
    if tuple(r[1])!=tuple(group[0][1]): continue
    before=s._group_expected_cost(group,len(group[0][1]))
    after=s._group_expected_cost(group+[r],len(group[0][1]))
    delta=after-before
    if delta<best_delta-1e-9: best_delta=delta; best=(c,k,r)
  if best is None: break
  c,k,r=best; sel[k].append(r); free.remove(c)
 return sel

def repair(sol,C,T,seconds=8.0):
 deadline=time.monotonic()+seconds; base=s._solution_expected_cost(sol,C,T); best_sol=sol; best=base
 by_key=collections.defaultdict(list)
 for r in s._canonical_candidates(C): by_key[r[0]].append(r)
 sel0=selected(sol,C)
 singles=[(k,rr) for k,rr in sel0.items() if len(rr[0][1])==1]
 # focus expensive/low p groups first
 singles.sort(key=lambda kv:s._group_expected_cost(kv[1],1),reverse=True)
 tried=0
 for (ka,ga),(kb,gb) in itertools.combinations(singles[:18],2):
  if time.monotonic()>deadline-.05: break
  ta=ga[0][1][0]; tb=gb[0][1][0]
  key1=','.join([ta,tb]); key2=','.join([tb,ta])
  rows=by_key.get(key1) or by_key.get(key2) or []
  if not rows: continue
  rows=sorted(rows,key=lambda r:(s._group_expected_cost([r],2),-r[4],r[5]))[:10]
  # old two groups consume old couriers; new bundle consumes 1-3, freed are redeployed
  old_c={r[2] for r in ga+gb}
  for k in range(1,min(3,len(rows))+1):
   for comb in itertools.combinations(rows,k):
    if time.monotonic()>deadline-.04: break
    cs=[r[2] for r in comb]
    if len(cs)!=len(set(cs)): continue
    # Can't use couriers already used outside removed groups.
    outside={r[2] for key,rr in sel0.items() if key not in (ka,kb) for r in rr}
    if any(c in outside for c in cs): continue
    newsel={key:list(rr) for key,rr in sel0.items() if key not in (ka,kb)}
    newsel[comb[0][0]]=list(comb)
    freed=(old_c-set(cs)) | (set(cs)&old_c and set())
    newsel=add_best_redundancy(newsel,C,T,freed,deadline)
    cand=[(key,[r[2] for r in rr]) for key,rr in newsel.items()]
    sc=s._solution_expected_cost(cand,C,T); tried+=1
    if sc<best-1e-9:
     best=sc; best_sol=cand; print('improve',best,'delta',best-base,'replace',ka,kb,'->',comb[0][0],cs,'tried',tried, flush=True)
     sel0=selected(best_sol,C); singles=[(k,rr) for k,rr in sel0.items() if len(rr[0][1])==1]; singles.sort(key=lambda kv:s._group_expected_cost(kv[1],1),reverse=True)
     return repair(best_sol,C,T,max(0.1,deadline-time.monotonic()))
 return best_sol,best,tried

def run(path):
 text=pathlib.Path(path).read_text(); C,T=parse(text); base_sol=s.solve(text); base=s._solution_expected_cost(base_sol,C,T)
 t=time.monotonic(); sol,score,tried=repair(base_sol,C,T,8.4)
 print(json.dumps({'case':pathlib.Path(path).name,'base':base,'compress':score,'delta':score-base,'groups':len(sol),'tried':tried,'time':time.monotonic()-t},ensure_ascii=False))
 if score<base-1e-9: print(sol)
if __name__=='__main__':
 for p in sys.argv[1:]: run(p)
