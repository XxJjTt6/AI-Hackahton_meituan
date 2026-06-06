#!/usr/bin/env python3
import glob, hashlib, importlib.machinery, importlib.util, json, statistics, sys, time, traceback
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'
paths=[]
for pat in [
 'solver.py',
 'solver_variants/solver_best_*.py',
 'solver_variants_v2/solver_v2_*.py',
 'solver_variants_v3/solver_v3_*.py',
 'solver_variants_v4/solver_v4_*.py',
 'solver_variants_v5/solver_v5_*.py',
 'solver_variants_v6/solver_v6_*.py',
 'runs/probe_*.py',
 'runs/guard_*.py',
 'runs/lag_*.py',
 'runs/pair_*.py',
]:
    paths += [ROOT/p for p in glob.glob(pat)]
seen=set(); uniq=[]
known_bad={
'c79ee39ae91035caef21de8eeda7685e764ecd6287f5d5c6c130d09f1a59e14e','3e0a88d2dfb3a69e4937916c2424280d961c9755bc9852522179fe02dc69b9c1',
'6395cbc62e94d9f3d46508f93137f2056da5c05059a75936811070da83cab14f','c0a0a8406e355c1dd4669764f6c614aa1519ae8fda689734e3c43b724059ee08','d8a471261b2961cdd16f2b0d79d10ba87b54caddbf92dab73f940c34a1c33743','23299900e98ad6128fdbe6256933863d475890b180d0dbb7f5fa164c5cffb8f8'
}
for p in paths:
    try:
        b=p.read_bytes(); sha=hashlib.sha256(b).hexdigest()
        if sha in seen: continue
        seen.add(sha); uniq.append((p,sha,len(b)))
    except Exception: pass

def load(path):
    name='scan_'+hashlib.md5(str(path).encode()).hexdigest()
    loader=importlib.machinery.SourceFileLoader(name,str(path)); spec=importlib.util.spec_from_loader(name,loader)
    m=importlib.util.module_from_spec(spec); loader.exec_module(m); return m

def eval_mod(m):
    cases=[('large',DATA.read_text(),1),('low025',proxy_eval.make_low(.25),1),('scarce40',proxy_eval.make_scarce(),2)]
    rows=[]
    for cname,text,trials in cases:
        parsed,tasks,couriers=proxy_eval.parse(text); T=set(tasks); vals=[]; times=[]; groups=[]
        for _ in range(trials):
            t=time.monotonic(); r=m.solve(text); times.append(time.monotonic()-t)
            vals.append(m._solution_expected_cost(r,parsed,T) if hasattr(m,'_solution_expected_cost') else 9999)
            groups.append(len(r))
        rows.append({'case':cname,'mean':statistics.mean(vals),'best':min(vals),'worst':max(vals),'time':statistics.mean(times),'groups':groups,'vals':vals})
    return rows

def score(rows):
    d={r['case']:r for r in rows}
    # baseline rough: large 657.1, low may fluctuate 1891/1922, scarce 1097.85
    return (d['large']['mean']-657.104)*4 + (d['low025']['mean']-1891.05)*.4 + (d['scarce40']['mean']-1097.85)*.8 + max(0,d['large']['time']-9.2)*30 + max(0,d['scarce40']['time']-9.8)*20 + (0 if min(d['scarce40']['groups'])>=39 else 40)

out=[]
print(f'[scan_start] candidates={len(uniq)}',flush=True)
for i,(p,sha,size) in enumerate(uniq,1):
    if size>=80000: continue
    try:
        text=p.read_text(errors='ignore')
        if 'def solve' not in text: continue
        m=load(p)
        if not hasattr(m,'solve'): continue
        rows=eval_mod(m); sc=score(rows)
        item={'score':sc,'path':str(p.relative_to(ROOT)),'sha':sha,'size':size,'known':sha in known_bad,'rows':rows}
        out.append(item)
        print(f"[scan] {i}/{len(uniq)} score={sc:.2f} known={sha in known_bad} {p.relative_to(ROOT)} sha={sha[:8]} rows="+json.dumps(rows,ensure_ascii=False),flush=True)
    except Exception as e:
        print(f'[scan_error] {p.relative_to(ROOT)} {type(e).__name__}: {e}',flush=True)
        traceback.print_exc(limit=1)
out=sorted(out,key=lambda x:x['score'])
(ROOT/'runs/hourly_candidate_scan_latest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('[scan_top] '+json.dumps(out[:10],ensure_ascii=False),flush=True)
