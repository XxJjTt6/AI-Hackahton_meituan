#!/usr/bin/env python3
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
START_TS=dt.datetime(2026,5,17,1,12,47)
END_TS=dt.datetime(2026,5,17,4,12,47)
LOG=ROOT/'runs'/f'agent_3h_loop_{dt.datetime.now():%Y%m%d_%H%M%S}.log'
LATEST=ROOT/'runs'/'agent_3h_loop_latest.log'
try:
    if LATEST.exists() or LATEST.is_symlink(): LATEST.unlink()
    LATEST.symlink_to(LOG.name)
except Exception: pass

def log(msg):
    line=f'{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}'
    print(line, flush=True)
    with LOG.open('a',encoding='utf-8') as f: f.write(line+'\n')

def run(cmd,timeout=120):
    log('$ '+' '.join(cmd))
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        with LOG.open('a',encoding='utf-8') as f:
            f.write(p.stdout[-6000:])
            if p.stdout and not p.stdout.endswith('\n'): f.write('\n')
            f.write(f'[exit {p.returncode}]\n')
        return p.returncode
    except Exception as e:
        log(f'[error] {e!r}')
        return 99
log(f'[start] adjusted target start={START_TS} end={END_TS}')
while dt.datetime.now() < END_TS:
    remaining=(END_TS-dt.datetime.now()).total_seconds()/60
    log(f'[tick] remaining_min={remaining:.1f}')
    run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py'],timeout=60)
    run([sys.executable,'_bench.py','solver.py','1'],timeout=45)
    sleep_for=min(300,max(5,(END_TS-dt.datetime.now()).total_seconds()))
    log(f'[sleep] {sleep_for:.1f}s')
    time.sleep(sleep_for)
log('[done] 3h target reached')
