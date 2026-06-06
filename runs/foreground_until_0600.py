#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
END_TS=dt.datetime(2026,5,17,6,0,0)
LOG=ROOT/'runs'/f'foreground_until_0600_{dt.datetime.now():%Y%m%d_%H%M%S}.log'
LATEST=ROOT/'runs'/'foreground_until_0600_latest.log'
try:
    if LATEST.exists() or LATEST.is_symlink(): LATEST.unlink()
    LATEST.symlink_to(LOG.name)
except Exception:
    pass

def log(msg):
    line=f'{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}'
    print(line, flush=True)
    with LOG.open('a',encoding='utf-8') as f:
        f.write(line+'\n')

def run(cmd, timeout=120):
    log('$ '+' '.join(cmd))
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        out=p.stdout[-5000:]
        print(out, end='' if out.endswith('\n') else '\n', flush=True)
        with LOG.open('a',encoding='utf-8') as f:
            f.write(out)
            if out and not out.endswith('\n'): f.write('\n')
            f.write(f'[exit {p.returncode}]\n')
        return p.returncode, out
    except Exception as e:
        log(f'[error] {e!r}')
        return 99, repr(e)

def solver_fingerprint():
    b=(ROOT/'solver.py').read_bytes()
    return len(b), hashlib.sha256(b).hexdigest()

log(f'[start_foreground] target_end={END_TS}')
size,sha=solver_fingerprint()
log(f'[baseline] solver.py size={size} sha256={sha}')
iteration=0
while dt.datetime.now() < END_TS:
    iteration += 1
    remaining=(END_TS-dt.datetime.now()).total_seconds()/60
    log(f'[iter {iteration}] remaining_min={remaining:.1f}')
    size,sha=solver_fingerprint()
    log(f'[solver] size={size} sha256={sha}')
    run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py'],timeout=60)
    run([sys.executable,'_bench.py','solver.py','1'],timeout=45)
    # Lightweight local probe every cycle; no official submit here.
    probe_code = r'''
import sys,time
from pathlib import Path
sys.path.insert(0,'runs')
import proxy_eval
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
mod=proxy_eval.load(ROOT/'solver.py')
for name,text in [('low025',proxy_eval.make_low(.25)),('scarce40',proxy_eval.make_scarce())]:
 rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
 t0=time.monotonic(); res=mod.solve(text); dt=time.monotonic()-t0
 cost=mod._solution_expected_cost(res,rows,T)
 print(f'{name}: time={dt:.2f}s proxy={cost:.2f} groups={len(res)}')
'''
    run([sys.executable,'-c',probe_code],timeout=70)
    sleep_for=min(300,max(5,(END_TS-dt.datetime.now()).total_seconds()))
    log(f'[sleep_foreground] {sleep_for:.1f}s')
    time.sleep(sleep_for)
log('[done] foreground target reached 06:00')
