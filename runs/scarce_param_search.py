#!/usr/bin/env python3
import datetime as dt, itertools, re, statistics, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import proxy_eval
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
BASE=(ROOT/'solver.py').read_text()
LOG=ROOT/'runs'/f'scarce_param_search_{dt.datetime.now():%Y%m%d_%H%M%S}.log'
LATEST=ROOT/'runs'/'scarce_param_search_latest.log'
try:
    if LATEST.exists() or LATEST.is_symlink(): LATEST.unlink()
    LATEST.symlink_to(LOG.name)
except Exception: pass

def log(s):
    line=f'{dt.datetime.now():%Y-%m-%d %H:%M:%S} {s}'
    print(line, flush=True)
    with LOG.open('a',encoding='utf-8') as f: f.write(line+'\n')

def write(name,text):
    p=ROOT/'runs'/f'scarce_{name}.py'; p.write_text(text); return p
text=proxy_eval.make_scarce(); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
configs=[]
for margin,beam,trigger in [(1.4,.35,'len'),(1.3,.4,'len'),(1.2,.5,'len'),(1.1,.55,'len'),(1.0,.6,'len'),(.9,.5,'lenm1')]:
    configs.append((margin,beam,trigger))
log('[start] scarce param search')
for margin,beam,trigger in configs:
    src=BASE
    cond='AE<len(B)' if trigger=='len' else 'AE<len(B)-1'
    src=re.sub(r'if G and AE<len\(B\)(?:-1)? and time\.monotonic\(\)<A-[0-9.]+:\n\t\t\tz=_sparse_beam_search\(C,B,min\(A,time\.monotonic\(\)\+[A-Za-z0-9_.]+\),coverage_first=_B\)',
               f'if G and {cond} and time.monotonic()<A-{margin}:\n\t\t\tz=_sparse_beam_search(C,B,min(A,time.monotonic()+{beam}),coverage_first=_B)', src, count=1)
    name=f'm{margin}_b{beam}_{trigger}'.replace('.','p')
    p=write(name,src)
    mod=proxy_eval.load(p); vals=[]; times=[]; groups=[]
    for i in range(5):
        t0=time.monotonic(); res=mod.solve(text); elapsed=time.monotonic()-t0
        vals.append(mod._solution_expected_cost(res,rows,T)); times.append(elapsed); groups.append(len(res))
    log(f'[cfg] {name} mean={statistics.mean(vals):.2f} best={min(vals):.2f} worst={max(vals):.2f} tmean={statistics.mean(times):.2f} groups={groups} vals={[round(v,2) for v in vals]}')
log('[done]')
