#!/usr/bin/env python3
import json, subprocess, sys, statistics, hashlib
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72'); SRC=ROOT/'solver.py'
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
CHILD=r'''
import importlib.util,json,sys,time,hashlib
from pathlib import Path
root=Path(sys.argv[1]); path=Path(sys.argv[2]); case=sys.argv[3]
sys.path.insert(0,str(root/'runs'))
import proxy_eval
texts={'official_like':(root/'runs/official_like_low_synth.txt').read_text(),'calibrated':(root/'runs/official_calibrated_low_synth.txt').read_text(),'low025':proxy_eval.make_low(.25),'low030':proxy_eval.make_low(.30),'large':proxy_eval.DATA.read_text(),'scarce40':proxy_eval.make_scarce()}
text=texts[case]; rows,tasks,c=proxy_eval.parse(text); T=set(tasks)
spec=importlib.util.spec_from_file_location('cand',str(path)); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
t=time.monotonic(); out=m.solve(text); dt=time.monotonic()-t
shape={}
for k,cs in out: shape[str(len(cs))]=shape.get(str(len(cs)),0)+1
print(json.dumps({'cost':m._solution_expected_cost(out,rows,T),'time':dt,'cov':m._solution_covered_count(out,rows),'sig':hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in out)).encode()).hexdigest()[:12],'shape':shape}))
'''
variants={
 'baseline': [],
 'worst_8_12_16': [('for(N,O)in((8,range(0,8)),(10,range(0,8)),(12,range(0,8))):','for(N,O)in((8,range(0,8)),(12,range(0,8)),(16,range(0,6))):')],
 'deep_8_12_16': [('for N in(8,10,12):\n\t\tfor O in range(10):','for N in(8,12,16):\n\t\tfor O in range(8):')],
 'late_16': [('F=(8,10,12,14)[B%4]','F=(8,10,12,14,16)[B%5]')],
 'all_wide': [('for(N,O)in((8,range(0,8)),(10,range(0,8)),(12,range(0,8))):','for(N,O)in((8,range(0,6)),(12,range(0,6)),(16,range(0,4))):'),('for N in(8,10,12):\n\t\tfor O in range(10):','for N in(8,12,16):\n\t\tfor O in range(7):'),('F=(8,10,12,14)[B%4]','F=(8,10,12,14,16)[B%5]')],
 'wide_more_repair_budget': [('if J and time.monotonic()<A-1.35:D=_low_deep_window_repair_solution(D,C,B,min(A,time.monotonic()+1.2))','if J and time.monotonic()<A-1.65:D=_low_deep_window_repair_solution(D,C,B,min(A,time.monotonic()+1.5))'),('if J and time.monotonic()<A-.95:D=_low_late_acceptance_repair_solution(D,C,B,min(A,time.monotonic()+.85))','if J and time.monotonic()<A-1.25:D=_low_late_acceptance_repair_solution(D,C,B,min(A,time.monotonic()+1.15))')],
}
def make(name,edits):
 s=SRC.read_text()
 for old,new in edits:
  if old not in s: raise SystemExit(f'missing edit {old[:80]}')
  s=s.replace(old,new,1)
 p=ROOT/'runs/night_20260526'/f'{name}.py'; p.write_text(s); return p
def run(p,case,n):
 rows=[]
 for _ in range(n):
  cp=subprocess.run([sys.executable,'-c',CHILD,str(ROOT),str(p),case],text=True,capture_output=True,timeout=45)
  rows.append(json.loads(cp.stdout) if cp.returncode==0 else {'err':cp.stderr[-800:] or cp.stdout[-800:]})
 return rows
def summ(rows):
 ok=[r for r in rows if 'cost' in r]
 if not ok: return {'ok':0,'rows':rows}
 return {'ok':len(ok),'mean':statistics.mean(r['cost'] for r in ok),'best':min(r['cost'] for r in ok),'worst':max(r['cost'] for r in ok),'time':statistics.mean(r['time'] for r in ok),'sigs':sorted({r['sig'] for r in ok}),'shapes':sorted({json.dumps(r['shape'],sort_keys=True) for r in ok}),'cov':sorted({r['cov'] for r in ok})}
report={}
for name,edits in variants.items():
 p=make(name,edits); report[name]={'sha':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size,'cases':{}}
 print('VAR',name,flush=True)
 for case in ['official_like','low025','low030','calibrated','large','scarce40']:
  n=2 if case in ('official_like','low025','low030') else 1
  rows=run(p,case,n); report[name]['cases'][case]={'runs':rows,'summary':summ(rows)}
  print(' ',case,report[name]['cases'][case]['summary'],flush=True)
(ROOT/'runs/night_20260526/round04_low_window_sweep.json').write_text(json.dumps(report,indent=2,sort_keys=True))
