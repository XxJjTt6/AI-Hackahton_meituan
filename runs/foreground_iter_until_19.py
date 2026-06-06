#!/usr/bin/env python3
import subprocess, sys, time, hashlib, json, re, os
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
base=(ROOT/'solver.py').read_text()
out=ROOT/'runs/fg_until19'; out.mkdir(exist_ok=True)

def write(name, text):
    p=out/(name+'.py'); p.write_text(text); return p

def repl(src, mapping):
    s=src
    for a,b in mapping.items():
        if a not in s:
            print(f'[skip-gen] missing pattern for {a[:60]}', flush=True); return None
        s=s.replace(a,b)
    return s

cands=[]
# Low-risk: small cache plus tighter time margin variants (should be no-op or safer, not submit unless official-cache-like).
for name, mp in {
    'time_868': {'A=i+8.7':'A=i+8.68'},
    'time_872': {'A=i+8.7':'A=i+8.72'},
    'scarce_time_882': {'if f:A=i+8.85':'if f:A=i+8.82'},
}.items():
    s=repl(base, mp)
    if s: cands.append(write(name,s))
# Business objective variants isolated to hard-scarce picker (not submitted unless local structural signal strong).
biz_func='''\ndef _hard_scarce_business_cost(result,candidates,all_tasks):\n\tK={(a[0],a[2]):a for a in candidates};covered=set();used=set();cost=_C;risk=_C;groups=0\n\tfor key,cs in result:\n\t\trows=[]\n\t\tfor c in cs:\n\t\t\tr=K.get((key,c))\n\t\t\tif r is _A or c in used:return float(_F)\n\t\t\tused.add(c);rows.append(r)\n\t\tif not rows:return float(_F)\n\t\tfor t in rows[0][1]:\n\t\t\tif t in covered:return float(_F)\n\t\t\tcovered.add(t)\n\t\tD=len(rows[0][1]);gc=_group_expected_cost(rows,D);cost+=gc;groups+=1\n\t\tp=1.0\n\t\tfor r in rows:p*=(1-r[4])\n\t\tp=1-p\n\t\trisk+=max(_C,gc-100.*D)*.12+max(_C,.62-p)*6.*D\n\treturn cost+100.*(len(all_tasks)-len(covered))+risk+groups*.02\n'''
if 'def _pick_hard_scarce_best' in base and 'return min(E,key=lambda s:(_hard_scarce_shadow_cost(s,B,C),_solution_expected_cost(s,B,C)))' in base:
    s=base.replace('def _pick_hard_scarce_best',biz_func+'\ndef _pick_hard_scarce_best')
    s=s.replace('return min(E,key=lambda s:(_hard_scarce_shadow_cost(s,B,C),_solution_expected_cost(s,B,C)))','return min(E,key=lambda s:(_hard_scarce_business_cost(s,B,C),_hard_scarce_shadow_cost(s,B,C),_solution_expected_cost(s,B,C)))')
    cands.append(write('biz_scarce_risk_tiny',s))
# Low robust selector no-op tests.
for th in [20,30]:
    s=repl(base, {'if H<=C+25.:return F':f'if H<=C+{th}.:return F'})
    if s: cands.append(write(f'low_accept_{th}',s))

print(f'[fg] generated {len(cands)} candidates at {time.strftime("%H:%M:%S")}', flush=True)
for p in cands:
    print(f'\n[fg] validating {p.name}', flush=True)
    try:
        r=subprocess.run([sys.executable,'_bench.py',str(p),'1'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=35)
        print(r.stdout, flush=True)
        if r.returncode: continue
        r=subprocess.run([sys.executable,'runs/proxy_eval.py','solver.py',str(p)],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=95)
        txt=r.stdout
        # print compact tail and extract candidate section
        parts=txt.split('solver ')
        print('[proxy-summary]\n' + txt[-1800:], flush=True)
    except subprocess.TimeoutExpired:
        print('[fg] timeout -> reject', flush=True)
