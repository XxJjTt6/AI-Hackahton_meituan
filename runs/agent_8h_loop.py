#!/usr/bin/env python3
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path
ROOT = Path('/Users/比赛/FOR_AutoSolver_706.72')
LOG = ROOT / 'runs' / f'agent_8h_loop_{dt.datetime.now():%Y%m%d_%H%M%S}.log'
LATEST = ROOT / 'runs' / 'agent_8h_loop_latest.log'
try:
    if LATEST.exists() or LATEST.is_symlink():
        LATEST.unlink()
    LATEST.symlink_to(LOG.name)
except Exception:
    pass
end = time.time() + 8*60*60
iter_no = 0

def log(msg):
    line = f'{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}'
    print(line, flush=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')

def run(cmd, timeout=None):
    log('$ ' + ' '.join(cmd))
    try:
        p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        out = p.stdout[-6000:]
        with LOG.open('a', encoding='utf-8') as f:
            f.write(out)
            if out and not out.endswith('\n'):
                f.write('\n')
            f.write(f'[exit {p.returncode}]\n')
        return p.returncode
    except subprocess.TimeoutExpired as e:
        with LOG.open('a', encoding='utf-8') as f:
            f.write((e.stdout or '')[-6000:] if isinstance(e.stdout, str) else '')
            f.write('[timeout]\n')
        return 124

log(f'[start] root={ROOT} end={dt.datetime.fromtimestamp(end):%Y-%m-%d %H:%M:%S}')
run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py'], timeout=60)
while time.time() < end:
    iter_no += 1
    log(f'[iter {iter_no}] remaining_min={(end-time.time())/60:.1f}')
    run([sys.executable, '_bench.py', 'solver.py', '1'], timeout=40)
    run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py'], timeout=60)
    sleep_for = min(60, max(1, end-time.time()))
    log(f'[sleep] {sleep_for:.1f}s')
    time.sleep(sleep_for)
log('[done]')
