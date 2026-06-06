#!/usr/bin/env python3
import importlib.util
spec=importlib.util.spec_from_file_location('m','runs/scarce_cache_full_column_repack.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
tasks={f'T{i:04d}' for i in range(40)}
cache=[('T0000,T0027', ['C005']), ('T0001,T0035', ['C018']), ('T0002,T0038', ['C009']), ('T0003,T0024', ['C012']), ('T0004,T0018', ['C007']), ('T0005,T0036', ['C019']), ('T0006,T0030', ['C003']), ('T0007,T0008', ['C001']), ('T0009,T0011', ['C014']), ('T0010,T0029', ['C004']), ('T0012,T0019', ['C010']), ('T0013,T0039', ['C013']), ('T0014,T0031', ['C008']), ('T0015,T0034', ['C015']), ('T0016', ['C000']), ('T0017,T0032', ['C002']), ('T0020,T0023', ['C016']), ('T0021,T0026', ['C017']), ('T0022,T0037', ['C011']), ('T0025,T0028', ['C006'])]
def build(cheap=True):
 rows=[];idx=0;used={c for k,cs in cache for c in cs}
 for k,cs in cache:
  for c in cs: rows.append((k,tuple(k.split(',')),c,50.0,1.0,idx));idx+=1
 for i in range(40):
  c=f'C{i:03d}'
  if c not in used: rows.append(('T0033',('T0033',),c,10.0 if cheap else 300.0,1.0,idx));idx+=1
 return rows
for cheap in (True,False):
 rows=build(cheap);out=m._scarce_full_column_repack(cache,rows,tasks)
 print('cheap',cheap,'returned',out is not None)
 if out:
  cov={t for k,cs in out for t in k.split(',')}
  print(' cov',len(cov),'has33','T0033' in cov,'cost',m._solution_expected_cost(out,rows,tasks),'base',m._solution_expected_cost(cache,rows,tasks))
