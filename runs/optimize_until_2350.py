#!/usr/bin/env python3
import datetime as dt
import hashlib
import itertools
import json
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
END_TS=dt.datetime(2026,5,17,23,50,0)
BASE_SOLVER=ROOT/'solver.py'
RUNS=ROOT/'runs'
LOG=RUNS/f'optimize_until_2350_{dt.datetime.now():%Y%m%d_%H%M%S}.log'
LATEST=RUNS/'optimize_until_2350_latest.log'
BEST_JSON=RUNS/'candidate_leaderboard_latest.json'
try:
    if LATEST.exists() or LATEST.is_symlink(): LATEST.unlink()
    LATEST.symlink_to(LOG.name)
except Exception:
    pass

def log(msg):
    line=f'{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}'
    print(line, flush=True)
    with LOG.open('a',encoding='utf-8') as f: f.write(line+'\n')

def sh(cmd,timeout=120,quiet=False):
    if not quiet: log('$ '+' '.join(map(str,cmd)))
    try:
        p=subprocess.run(list(map(str,cmd)),cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        if not quiet:
            out=p.stdout[-5000:]
            print(out,end='' if out.endswith('\n') else '\n',flush=True)
            with LOG.open('a',encoding='utf-8') as f:
                f.write(out)
                if out and not out.endswith('\n'): f.write('\n')
                f.write(f'[exit {p.returncode}]\n')
        return p.returncode,p.stdout
    except Exception as e:
        log(f'[cmd_error] {e!r}')
        return 99,repr(e)

def fp(path):
    b=Path(path).read_bytes(); return len(b),hashlib.sha256(b).hexdigest()

def write_learn(summary,details):
    ts=dt.datetime.now().strftime('%Y%m%d-%H%M%S')
    with (ROOT/'.learnings'/'LEARNINGS.md').open('a',encoding='utf-8') as f:
        f.write(f"\n## [LRN-{ts}] insight\n\n**Logged**: {dt.datetime.now().isoformat(timespec='seconds')}+08:00\n**Priority**: medium\n**Status**: observed\n**Area**: algorithm\n\n### Summary\n{summary}\n\n### Details\n{details}\n\n### Metadata\n- Source: foreground optimizer\n- Related Files: `solver.py`, `runs/optimize_until_2350_latest.log`\n- Tags: autosolver, local_search\n\n---\n")

def eval_variant(path,timeout=220):
    code=r'''
import importlib.machinery, importlib.util, json, sys, time, statistics
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
path=Path(sys.argv[1])
loader=importlib.machinery.SourceFileLoader('cand_'+str(abs(hash(str(path)))),str(path))
spec=importlib.util.spec_from_loader(loader.name,loader)
mod=importlib.util.module_from_spec(spec); loader.exec_module(mod)
cases=[('large', (ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt').read_text()),('low020',proxy_eval.make_low(.20)),('low025',proxy_eval.make_low(.25)),('low030',proxy_eval.make_low(.30)),('scarce40',proxy_eval.make_scarce())]
rows=[]
for name,text in cases:
    parsed,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
    trials=2 if name in ('scarce40','low025') else 1
    vals=[]; times=[]; groups=[]
    for _ in range(trials):
        t0=time.monotonic(); res=mod.solve(text); elapsed=time.monotonic()-t0
        vals.append(mod._solution_expected_cost(res,parsed,T)); times.append(elapsed); groups.append(len(res))
    rows.append({'case':name,'mean':statistics.mean(vals),'best':min(vals),'worst':max(vals),'time_mean':statistics.mean(times),'groups':groups})
print(json.dumps(rows,ensure_ascii=False))
'''
    rc,out=sh([sys.executable,'-c',code,str(path)],timeout=timeout,quiet=True)
    if rc: return None, out
    try: return json.loads(out.strip().splitlines()[-1]), ''
    except Exception as e: return None, out[-1000:]+repr(e)

def score_rows(rows):
    d={r['case']:r for r in rows}
    # weighted local proxy: protect large, emphasize low/scarce, penalize runtime and worst-case volatility
    score=0
    score += (d['large']['mean']-657.104)*2.0
    score += (d['low020']['mean']-2063.99)*0.15
    score += (d['low025']['mean']-1888.63)*0.6
    score += (d['low030']['mean']-1735.50)*0.25
    score += (d['scarce40']['mean']-1070.0)*0.8
    score += max(0,d['scarce40']['worst']-1097.85)*0.4
    score += max(0,d['large']['time_mean']-8.5)*10
    return score

def mutate(base_text,idx):
    variants=[]
    def add(name,text):
        variants.append((name,text))
    s=base_text
    # Known risky knobs, evaluated locally only.
    for th in [5,10,15,20,25,35]:
        add(f'low_picker_th{th}', s.replace('if H<=C+25.:return F',f'if H<=C+{float(th):g}:return F',1))
    for deep in ['(8,10,12,16)','(8,10,12,20)','(8,10,12,16,20)']:
        add('low_deep_'+deep.strip('()').replace(',','_'), s.replace('for N in(8,10,12):',f'for N in{deep}:',1))
    sparse_patterns=[
        ('scarce_sparse_early_short','if G and AE<len(B) and time.monotonic()<A-1.2:\n\t\t\tz=_sparse_beam_search(C,B,min(A,time.monotonic()+.5),coverage_first=_B)'),
        ('scarce_sparse_early_tiny','if G and AE<len(B) and time.monotonic()<A-1.35:\n\t\t\tz=_sparse_beam_search(C,B,min(A,time.monotonic()+.35),coverage_first=_B)'),
        ('scarce_sparse_mid','if G and AE<len(B)-1 and time.monotonic()<A-1.1:\n\t\t\tz=_sparse_beam_search(C,B,min(A,time.monotonic()+.55),coverage_first=_B)'),
    ]
    pat=r'if G and AE<len\(B\)-1 and time\.monotonic\(\)<A-\.9:\n\t\t\tz=_sparse_beam_search\(C,B,min\(A,time\.monotonic\(\)\+_E\),coverage_first=_B\)'
    for name,repl in sparse_patterns:
        add(name, re.sub(pat,repl,s,count=1))
    # time budget knobs for scarce branch: tiny variations
    add('scarce_time_895', s.replace('if f:A=i+8.85','if f:A=i+8.95',1))
    add('scarce_time_875', s.replace('if f:A=i+8.85','if f:A=i+8.75',1))
    # pair low picker with deep20 for local search only
    t=s.replace('if H<=C+25.:return F','if H<=C+10.:return F',1).replace('for N in(8,10,12):','for N in(8,10,12,20):',1)
    add('combo_low_th10_deep20',t)
    return variants

log(f'[start] target_end={END_TS}')
size,sha=fp(BASE_SOLVER); log(f'[baseline] size={size} sha={sha}')
sh([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py'],timeout=60)
sh([sys.executable,'_bench.py','solver.py','1'],timeout=45)
base_rows,err=eval_variant(BASE_SOLVER)
if base_rows:
    log('[baseline_proxy] '+json.dumps(base_rows,ensure_ascii=False))
else:
    log('[baseline_proxy_error] '+err)
base_text=BASE_SOLVER.read_text()
leader=[]
round_no=0
while dt.datetime.now()<END_TS:
    round_no+=1
    log(f'[round {round_no}] remaining_min={(END_TS-dt.datetime.now()).total_seconds()/60:.1f}')
    candidates=mutate(base_text,round_no)
    random.Random(round_no).shuffle(candidates)
    for name,text in candidates:
        if dt.datetime.now()>=END_TS: break
        path=RUNS/f'cand_{round_no}_{name}.py'
        path.write_text(text)
        rc,_=sh([sys.executable,'-m','py_compile',str(path)],timeout=20,quiet=True)
        if rc:
            log(f'[candidate_bad_compile] {name}')
            continue
        rows,err=eval_variant(path)
        if not rows:
            log(f'[candidate_error] {name} {err[:300]}')
            continue
        local_score=score_rows(rows)
        size,sha=fp(path)
        item={'score':local_score,'name':name,'path':str(path),'size':size,'sha':sha,'rows':rows,'time':dt.datetime.now().isoformat(timespec='seconds')}
        leader.append(item); leader=sorted(leader,key=lambda x:x['score'])[:20]
        BEST_JSON.write_text(json.dumps(leader,ensure_ascii=False,indent=2),encoding='utf-8')
        log(f"[candidate] {name} local_score={local_score:.3f} sha={sha[:8]} rows="+json.dumps(rows,ensure_ascii=False))
        # If a candidate is substantially better locally, save it but don't official-submit automatically.
        if local_score < -8:
            best_path=RUNS/f'HIGH_CONF_{name}_{sha[:8]}.py'
            shutil.copy(path,best_path)
            log(f'[high_conf_local_saved] {best_path} local_score={local_score:.3f}; official submit requires additional review/cache check')
            write_learn(f'High-confidence local candidate saved: {name}', f'Path `{best_path}`, local_score `{local_score:.3f}`, rows `{json.dumps(rows,ensure_ascii=False)}`. Not submitted automatically to save quota.')
    log('[leader_top] '+json.dumps(leader[:5],ensure_ascii=False))
log('[done] target reached 23:50')
