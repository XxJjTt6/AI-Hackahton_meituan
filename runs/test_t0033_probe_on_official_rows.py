#!/usr/bin/env python3
# Build a synthetic official-row table from official details and test helper behavior.
import json, importlib.util
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
spec=importlib.util.spec_from_file_location('m',ROOT/'runs/scarce_cache_t0033_mustcover_margin.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# Use official current best rows plus negative run rows as candidate rows. Scores/willingness cannot reproduce exact cost, so this only tests guards/path.
rows=[]; idx=0; tasks={f'T{i:04d}' for i in range(40)}
for fp in ['runs/official_submit_20260518_175316_f65d16ac.json','runs/official_submit_20260518_200532_94c02f02.json']:
 data=json.load(open(ROOT/fp)); cr=next(c for c in data['result']['case_results'] if c['case_file']=='scarce_couriers_seed401.txt')
 for d in cr['detail']:
  # approximate row with score=cost and p=1 just to create row keys; not meaningful for cost.
  for c in d['couriers']:
   k=d['task_id_list']; rows.append((k,tuple(k.split(',')),c,float(d['cost']),1.0,idx)); idx+=1
cache=m._scarce_seed401_cached_solution(rows,tasks,40,40,.3)
print('cache',cache is not None, len(cache) if cache else None)
try:
 out=m._scarce_t0033_two_replace_probe(cache,rows,tasks)
 print('probe returned',out)
except Exception as e:
 print('error',type(e).__name__,e)
