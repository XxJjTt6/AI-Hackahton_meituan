#!/usr/bin/env python3
"""Try to force the occasional best synthetic-low signatures earlier by targeted window order.
"""
import json, subprocess, sys, statistics, hashlib
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72'); SRC=ROOT/'solver.py'
CHILD=r'''
import importlib.util,json,sys,time,hashlib
from pathlib import Path
root=Path('/Users/比赛/FOR_AutoSolver_706.72'); path=Path(sys.argv[1]); case=sys.argv[2]
sys.path.insert(0,str(root/'runs'))
import proxy_eval
texts={'official_like':(root/'runs/official_like_low_synth.txt').read_text(),'low025':proxy_eval.make_low(.25),'low030':proxy_eval.make_low(.30),'calibrated':(root/'runs/official_calibrated_low_synth.txt').read_text(),'large':proxy_eval.DATA.read_text(),'scarce40':proxy_eval.make_scarce()}
text=texts[case]; rows,tasks,c=proxy_eval.parse(text); T=set(tasks)
spec=importlib.util.spec_from_file_location('cand',str(path)); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
t=time.monotonic(); out=m.solve(text); dt=time.monotonic()-t
print(json.dumps({'cost':m._solution_expected_cost(out,rows,T),'cov':m._solution_covered_count(out,rows),'time':dt,'sig':hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in out)).encode()).hexdigest()[:12]}))
'''
variants={
 'baseline':[],
 'worst_start_offset5':[('for(N,O)in((8,range(0,8)),(10,range(0,8)),(12,range(0,8))):','for(N,O)in((8,range(5,13)),(10,range(5,13)),(12,range(5,13))):')],
 'worst_start_offset2_16':[('for(N,O)in((8,range(0,8)),(10,range(0,8)),(12,range(0,8))):','for(N,O)in((16,range(2,8)),(12,range(2,10)),(8,range(2,8))):')],
 'deep_offset5':[('for N in(8,10,12):\n\t\tfor O in range(10):','for N in(12,10,8):\n\t\tfor O in range(5,15):')],
 'late_more_accept':[('if H<E-1e-09 or H<=O[V]+4.:N=L;E=H','if H<E-1e-09 or H<=O[V]+12.:N=L;E=H')],
 'late_less_accept':[('if H<E-1e-09 or H<=O[V]+4.:N=L;E=H','if H<E-1e-09 or H<=O[V]+1.:N=L;E=H')],
}
def make(name,edits):
 s=SRC.read_text()
 for old,new in edits:
  if old not in s: raise SystemExit('missing '+name)
  s=s.replace(old,new,1)
 p=ROOT/'runs/night_20260526'/f'round13_{name}.py'; p.write_text(s); return p
def run(p,case,n):
 out=[]
 for _ in range(n):
  cp=subprocess.run([sys.executable,'-c',CHILD,str(p),case],text=True,capture_output=True,timeout=45)
  out.append(json.loads(cp.stdout) if cp.returncode==0 else {'err':cp.stderr[-500:]})
 return out
def summ(rows):
 ok=[r for r in rows if 'cost' in r]
 return {'mean':statistics.mean(r['cost'] for r in ok),'best':min(r['cost'] for r in ok),'worst':max(r['cost'] for r in ok),'sigs':sorted({r['sig'] for r in ok}),'cov':sorted({r['cov'] for r in ok})} if ok else {'err':rows}
report={}
for name,edits in variants.items():
 p=make(name,edits); report[name]={}
 print('VAR',name,flush=True)
 for case in ['official_like','low025','low030','calibrated','large','scarce40']:
  n=3 if case in ('official_like','low025','low030') else 1
  rows=run(p,case,n); report[name][case]={'runs':rows,'summary':summ(rows)}
  print(' ',case,report[name][case]['summary'],flush=True)
(ROOT/'runs/night_20260526/round13_low_stable_best_signature_fix.json').write_text(json.dumps(report,indent=2,sort_keys=True))
