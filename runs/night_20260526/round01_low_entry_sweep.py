#!/usr/bin/env python3
import hashlib, importlib.util, json, subprocess, sys, tempfile, statistics, time
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
SRC=ROOT/'solver.py'
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
CASES={
 'official_like': (ROOT/'runs/official_like_low_synth.txt').read_text(),
 'calibrated': (ROOT/'runs/official_calibrated_low_synth.txt').read_text(),
 'large': proxy_eval.DATA.read_text(),
 'low025': proxy_eval.make_low(.25),
 'low030': proxy_eval.make_low(.30),
 'scarce40': proxy_eval.make_scarce(),
}
CHILD=r'''
import importlib.util,json,sys,time,hashlib
from pathlib import Path
root=Path(sys.argv[1]); path=Path(sys.argv[2]); case=sys.argv[3]
sys.path.insert(0,str(root/'runs'))
import proxy_eval
texts={
 'official_like': (root/'runs/official_like_low_synth.txt').read_text(),
 'calibrated': (root/'runs/official_calibrated_low_synth.txt').read_text(),
 'large': proxy_eval.DATA.read_text(),
 'low025': proxy_eval.make_low(.25),
 'low030': proxy_eval.make_low(.30),
 'scarce40': proxy_eval.make_scarce(),
}
text=texts[case]; rows,tasks,c=proxy_eval.parse(text); T=set(tasks)
spec=importlib.util.spec_from_file_location('cand', str(path)); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
t=time.monotonic(); out=m.solve(text); dt=time.monotonic()-t
cost=m._solution_expected_cost(out,rows,T); cov=m._solution_covered_count(out,rows)
sig=hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in out)).encode()).hexdigest()[:12]
shape={}
for k,cs in out: shape[str(len(cs))]=shape.get(str(len(cs)),0)+1
print(json.dumps({'case':case,'cost':cost,'time':dt,'cov':cov,'sig':sig,'shape':shape,'rows':len(out)}))
'''

def make_variant(name, edits):
    s=SRC.read_text()
    for old,new in edits:
        if old not in s: raise RuntimeError(f'{name} missing edit {old[:60]}')
        s=s.replace(old,new,1)
    p=ROOT/'runs/night_20260526'/f'{name}.py'
    p.write_text(s)
    return p

def run(path, case, n=1):
    out=[]
    for _ in range(n):
        cp=subprocess.run([sys.executable,'-c',CHILD,str(ROOT),str(path),case],text=True,capture_output=True,timeout=40)
        if cp.returncode: out.append({'case':case,'err':cp.stderr[-1000:] or cp.stdout[-1000:]})
        else: out.append(json.loads(cp.stdout))
    return out

def summary(rows):
    ok=[r for r in rows if 'cost' in r]
    if not ok: return {'ok':0,'rows':rows}
    return {'ok':len(ok),'mean':statistics.mean(r['cost'] for r in ok),'best':min(r['cost'] for r in ok),'worst':max(r['cost'] for r in ok),'time':statistics.mean(r['time'] for r in ok),'sigs':sorted({r['sig'] for r in ok}),'shapes':sorted({json.dumps(r['shape'],sort_keys=True) for r in ok}),'cov':sorted({r['cov'] for r in ok})}

variants={
 'baseline': [],
 'bias_recursion': [('if _D and J and not _LOW_BIAS_ACTIVE:', 'if _B and J and not _LOW_BIAS_ACTIVE:')],
 'scale_020_033_050': [('AC=(.25,_E/3.,.5)if J else(_E/3.,)', 'AC=(.2,_E/3.,.5)if J else(_E/3.,)')],
 'scale_025_040_055': [('AC=(.25,_E/3.,.5)if J else(_E/3.,)', 'AC=(.25,.4,.55)if J else(_E/3.,)')],
 'global_more_cols': [('top_riders_per_task_key=8,max_k=4,option_limit=28)', 'top_riders_per_task_key=10,max_k=5,option_limit=38)')],
 'low_col_more_cols': [('top_riders_per_task_key=10,max_k=3,option_limit=28)', 'top_riders_per_task_key=13,max_k=4,option_limit=44)')],
 'early_global_longer': [('p=_solve_low_global_column_search(C,B,min(A,time.monotonic()+.75))', 'p=_solve_low_global_column_search(C,B,min(A,time.monotonic()+1.15))')],
}
report={}
for name,edits in variants.items():
    p=make_variant(name,edits)
    report[name]={'sha':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size,'cases':{}}
    print('VAR',name,flush=True)
    for case in ['official_like','calibrated','low025','low030','large','scarce40']:
        n=2 if case in ('official_like','low025','low030') else 1
        rows=run(p,case,n)
        report[name]['cases'][case]={'runs':rows,'summary':summary(rows)}
        sm=report[name]['cases'][case]['summary']
        print(' ',case,sm,flush=True)
( ROOT/'runs/night_20260526/round01_low_entry_sweep.json').write_text(json.dumps(report,indent=2,sort_keys=True))
