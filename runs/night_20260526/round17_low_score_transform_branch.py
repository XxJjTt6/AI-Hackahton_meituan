#!/usr/bin/env python3
import json, subprocess, sys, statistics, hashlib
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72'); SRC=ROOT/'solver.py'
CHILD=r'''
import importlib.util,json,sys,time,hashlib
from pathlib import Path
root=Path('/Users/比赛/FOR_AutoSolver_706.72'); path=Path(sys.argv[1]); case=sys.argv[2]
sys.path.insert(0,str(root/'runs'))
import proxy_eval
texts={'official_like':(root/'runs/official_like_low_synth.txt').read_text(),'calibrated':(root/'runs/official_calibrated_low_synth.txt').read_text(),'low025':proxy_eval.make_low(.25),'low030':proxy_eval.make_low(.30),'large':proxy_eval.DATA.read_text(),'scarce40':proxy_eval.make_scarce()}
text=texts[case]; rows,tasks,c=proxy_eval.parse(text); T=set(tasks)
spec=importlib.util.spec_from_file_location('cand',str(path)); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
t=time.monotonic(); out=m.solve(text); dt=time.monotonic()-t
shape={}
for k,cs in out: shape[str(len(cs))]=shape.get(str(len(cs)),0)+1
print(json.dumps({'cost':m._solution_expected_cost(out,rows,T),'cov':m._solution_covered_count(out,rows),'time':dt,'sig':hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in out)).encode()).hexdigest()[:12],'shape':shape}))
'''
insert_after="J=F and not G and L==30 and d>=50 and A9<.25\n"
variants={
 'baseline':'',
 'low_score_discount_high_w':'\tif J:C=[(a,b,c,d0*(1-.25*e0),e0,f0) for (a,b,c,d0,e0,f0) in C]\n',
 'low_score_discount_low_w':'\tif J:C=[(a,b,c,d0*(.8+.8*e0),e0,f0) for (a,b,c,d0,e0,f0) in C]\n',
 'low_score_bundle_bonus':'\tif J:C=[(a,b,c,d0*(.92 if len(b)>1 else 1.05),e0,f0) for (a,b,c,d0,e0,f0) in C]\n',
 'low_score_single_bonus':'\tif J:C=[(a,b,c,d0*(1.08 if len(b)>1 else .9),e0,f0) for (a,b,c,d0,e0,f0) in C]\n',
}
def make(name,code):
 s=SRC.read_text()
 if code:
  if insert_after not in s: raise SystemExit('insert target missing')
  s=s.replace(insert_after,insert_after+code,1)
 p=ROOT/'runs/night_20260526'/f'round17_{name}.py'; p.write_text(s); return p
def run(p,case,n):
 rows=[]
 for _ in range(n):
  cp=subprocess.run([sys.executable,'-c',CHILD,str(p),case],text=True,capture_output=True,timeout=45)
  rows.append(json.loads(cp.stdout) if cp.returncode==0 else {'err':cp.stderr[-500:]})
 return rows
def summ(rows):
 ok=[r for r in rows if 'cost' in r]
 return {'mean':statistics.mean(r['cost'] for r in ok),'best':min(r['cost'] for r in ok),'worst':max(r['cost'] for r in ok),'sigs':sorted({r['sig'] for r in ok}),'shapes':sorted({json.dumps(r['shape'],sort_keys=True) for r in ok}),'cov':sorted({r['cov'] for r in ok})} if ok else {'err':rows}
report={}
for name,code in variants.items():
 p=make(name,code); report[name]={}; print('VAR',name,flush=True)
 for case in ['official_like','calibrated','low025','low030','large','scarce40']:
  n=2 if case in ('official_like','low025','low030') else 1
  rows=run(p,case,n); report[name][case]={'runs':rows,'summary':summ(rows)}
  print(' ',case,report[name][case]['summary'],flush=True)
(ROOT/'runs/night_20260526/round17_low_score_transform_branch.json').write_text(json.dumps(report,indent=2,sort_keys=True))
