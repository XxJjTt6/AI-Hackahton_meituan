#!/usr/bin/env python3
import importlib.util
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
spec=importlib.util.spec_from_file_location('m',ROOT/'runs/scarce_cache_t0033_mustcover_margin.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
tasks={f'T{i:04d}' for i in range(40)}
cache=[('T0000,T0027', ['C005']), ('T0001,T0035', ['C018']), ('T0002,T0038', ['C009']), ('T0003,T0024', ['C012']), ('T0004,T0018', ['C007']), ('T0005,T0036', ['C019']), ('T0006,T0030', ['C003']), ('T0007,T0008', ['C001']), ('T0009,T0011', ['C014']), ('T0010,T0029', ['C004']), ('T0012,T0019', ['C010']), ('T0013,T0039', ['C013']), ('T0014,T0031', ['C008']), ('T0015,T0034', ['C015']), ('T0016', ['C000']), ('T0017,T0032', ['C002']), ('T0020,T0023', ['C016']), ('T0021,T0026', ['C017']), ('T0022,T0037', ['C011']), ('T0025,T0028', ['C006'])]
# rows: all cache rows with p=1 and score chosen to approximate current costs low enough.
rows=[]; idx=0
costs={'T0001,T0035':107.8965,'T0020,T0023':89.2482,'T0025,T0028':71.0059,'T0033':10.0,'T0028,T0033':20.0}
for k,cs in cache:
    for c in cs:
        rows.append((k,tuple(k.split(',')),c,costs.get(k,50.0),1.0,idx)); idx+=1
# add all couriers not used to satisfy cache guard if needed and candidate replacement rows.
for i in range(40):
    c=f'C{i:03d}'
    if all(r[2]!=c for r in rows):
        rows.append(('T0033',('T0033',),c,200.0,1.0,idx)); idx+=1
# add cheap row using removed courier C006 to cover T0028,T0033 if replacing T0025,T0028.
rows.append(('T0028,T0033',('T0028','T0033'),'C006',220.0,1.0,idx)); idx+=1
out=m._scarce_t0033_two_replace_probe(cache,rows,tasks)
print('returned',out is not None)
if out:
    covered={t for k,cs in out for t in k.split(',')}
    print('covered',len(covered),'hasT0033','T0033' in covered,'cost',m._solution_expected_cost(out,rows,tasks),'base',m._solution_expected_cost(cache,rows,tasks))
    print([x for x in out if 'T0033' in x[0]])
