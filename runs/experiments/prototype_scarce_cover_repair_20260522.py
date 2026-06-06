#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,pathlib,time,sys,json,collections
ROOT=pathlib.Path(__file__).resolve().parents[2]
SOLVER=ROOT/'runs/baselines/official_best_7046558e_robust_cache.py'
spec=importlib.util.spec_from_file_location('s',SOLVER); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
# import stress generator helpers
spec2=importlib.util.spec_from_file_location('stress',ROOT/'runs/experiments/stress_scan_autosolver_20260522.py'); stress=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(stress)

def parse(text):
 rows=[];T=set();lines=text.strip().splitlines();st=1 if lines and lines[0].startswith('task') else 0
 for i,l in enumerate(lines[st:]):
  p=l.split('\t');ts=tuple(x.strip() for x in p[0].split(',') if x.strip());rows.append((p[0],ts,p[1],float(p[2]),float(p[3]),i));T.update(ts)
 return rows,T

def cheap_cover(C,T,deadline):
 # Try sparse cover coverage-first + bundle group MCF + pick by hard-scarce shadow.
 E=[]
 for mode in [True,False]:
  if time.monotonic()<deadline-.2:
   x=s._sparse_beam_search(C,T,min(deadline,time.monotonic()+.6),coverage_first=mode)
   if x:E.append(x)
 if time.monotonic()<deadline-.5:
  x=s._solve_scarce_bundle_mcf_enum(C,T,min(deadline,time.monotonic()+.8))
  if x:E.append(x)
 if time.monotonic()<deadline-.5:
  x=s._solve_scarce_bundle_group_mcf_enum(C,T,min(deadline,time.monotonic()+.8))
  if x:E.append(x)
 if not E:return []
 return min(E,key=lambda r:(len(T)-s._solution_covered_count(r,C),s._solution_expected_cost(r,C,T)))

def run_variant(nt,nc,ws,bs):
 rows,tasks,couriers=stress.parse(stress.DATA.read_text())
 text=stress.subset_variant(rows,tasks,couriers,nt,nc,wscale=ws,score_scale=.82 if ws<.5 else 1.0,bundle_scale=bs,seed=nt*100+nc)
 C,T=parse(text); t=time.monotonic(); base=s.solve(text); bt=time.monotonic()-t; bc=s._solution_expected_cost(base,C,T); bcov=s._solution_covered_count(base,C)
 t=time.monotonic(); cov=cheap_cover(C,T,time.monotonic()+8.5); ct=time.monotonic()-t; cc=s._solution_expected_cost(cov,C,T) if cov else 1e9; ccov=s._solution_covered_count(cov,C) if cov else 0
 print(json.dumps({'nt':nt,'nc':nc,'ws':ws,'bs':bs,'base':bc,'bcov':bcov,'bt':bt,'cover':cc,'ccov':ccov,'ct':ct,'delta':cc-bc},ensure_ascii=False))
if __name__=='__main__':
 for args in [(40,40,.22,.55),(40,40,.22,1.0),(40,40,.3,.55),(40,40,.3,1.0),(40,40,.7,.55),(40,40,1.0,1.0)]: run_variant(*args)
