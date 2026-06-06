#!/usr/bin/env python3
import datetime as dt
import itertools
import re
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import proxy_eval
ROOT = Path('/Users/比赛/FOR_AutoSolver_706.72')
LOG = ROOT/'runs'/f'auto_explore_{dt.datetime.now():%Y%m%d_%H%M%S}.log'
LATEST = ROOT/'runs'/'auto_explore_latest.log'
try:
    if LATEST.exists() or LATEST.is_symlink(): LATEST.unlink()
    LATEST.symlink_to(LOG.name)
except Exception: pass
END = time.time() + 8*60*60
BASE = (ROOT/'solver.py').read_text()

def log(s):
    line=f'{dt.datetime.now():%Y-%m-%d %H:%M:%S} {s}'
    print(line, flush=True)
    with LOG.open('a', encoding='utf-8') as f: f.write(line+'\n')

def write_variant(name, text):
    path=ROOT/'runs'/f'auto_{name}.py'
    path.write_text(text)
    try:
        subprocess.run([sys.executable, '-m', 'py_compile', str(path)], cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10)
    except Exception as e:
        log(f'[bad_compile] {name} {e}')
        return None
    return path

def eval_variant(path, cases):
    mod=proxy_eval.load(path)
    total=0.0; rows=[]
    for cname,text in cases:
        parsed,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
        t0=time.monotonic(); res=mod.solve(text); elapsed=time.monotonic()-t0
        cost=mod._solution_expected_cost(res, parsed, T); total += cost
        kd={}
        for k,cs in res: kd[len(cs)]=kd.get(len(cs),0)+1
        rows.append((cname, elapsed, cost, len(res), kd))
    return total, rows

low_cases=[(f'low{s:.2f}', proxy_eval.make_low(s)) for s in (0.20,0.25,0.30,0.35)]
scarce_cases=[('scarce40', proxy_eval.make_scarce())]
log('[start] auto explore')
best=[]
# Low picker/window sweep, cheap and deterministic enough.
thresholds=[0,5,10,15,20,25,35]
deep_opts=['(8,10,12)','(8,10,12,16)','(8,10,12,20)','(8,10,12,16,20)']
late_opts=['(8,10,12,14)','(8,10,12,14,16)','(8,10,12,14,16,18)']
for th,deep,late in itertools.product(thresholds, deep_opts, late_opts):
    if time.time()>END: break
    text=BASE
    text=text.replace('if H<=C+10.:return F', f'if H<=C+{float(th):g}:return F', 1)
    text=re.sub(r'for N in\([0-9,]+\):\n\t\tfor O in range\(10\):', f'for N in{deep}:\n\t\tfor O in range(10):', text, count=1)
    text=re.sub(r'F=\([0-9,]+\)\[B%\d+\];K=B%5', f'F={late}[B%{late.count(",")+1}];K=B%5', text, count=1)
    name=f'low_th{th}_d{deep.replace(",", "_").replace("(", "").replace(")", "")}_l{late.replace(",", "_").replace("(", "").replace(")", "")}'
    path=write_variant(name, text)
    if not path: continue
    try:
        total, rows=eval_variant(path, low_cases)
    except Exception as e:
        log(f'[bad_eval] {name} {e}')
        continue
    best.append((total,name,rows))
    detail='; '.join(f'{c}:t={t:.2f},cost={cost:.2f},g={g}' for c,t,cost,n,g in rows)
    log(f'[low] total={total:.2f} {name} {detail}')
    best=sorted(best)[:10]
log('[best_low]')
for total,name,rows in sorted(best)[:10]:
    log(f'  {total:.2f} {name}')
# Periodic baseline/scarce monitoring for the rest of the requested duration.
iter_no=0
while time.time()<END:
    iter_no+=1
    try:
        total, rows=eval_variant(ROOT/'solver.py', [('large', (ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt').read_text())]+scarce_cases+low_cases[:2])
        detail='; '.join(f'{c}:t={t:.2f},cost={cost:.2f},g={g}' for c,t,cost,n,g in rows)
        log(f'[monitor {iter_no}] total={total:.2f} {detail}')
    except Exception as e:
        log(f'[monitor_err] {e}')
    time.sleep(180)
log('[done]')
