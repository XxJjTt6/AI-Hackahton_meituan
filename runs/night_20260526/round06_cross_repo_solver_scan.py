#!/usr/bin/env python3
import hashlib, json, subprocess, sys, statistics, shutil
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
cands=[]
for base in [Path('/Users/比赛/FOR_AutoSolver_706.72'),Path('/Users/比赛/FOR_AutoSolver_new_start'),Path('/Users/比赛/FOR_AutoSolver_xjt4claude'),Path('/Users/比赛/FOR_AutoSolver_bendigai'),Path('/Users/比赛/true_new_start_meituan')]:
    for p in base.rglob('solver*.py'):
        if '__pycache__' in p.parts or p.stat().st_size>90000: continue
        cands.append(p)
seen={}; uniq=[]
for p in cands:
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h not in seen:
        seen[h]=p; uniq.append((h,p))
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
cost=m._solution_expected_cost(out,rows,T) if hasattr(m,'_solution_expected_cost') else None
cov=m._solution_covered_count(out,rows) if hasattr(m,'_solution_covered_count') else None
print(json.dumps({'cost':cost,'time':dt,'cov':cov,'n':len(out),'sig':hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in out)).encode()).hexdigest()[:12]}))
'''
report=[]
for h,p in uniq:
    rec={'path':str(p),'sha':h,'size':p.stat().st_size,'cases':{}}
    print('SCAN',h[:8],p,flush=True)
    for case in ['official_like','calibrated','low025','low030','large','scarce40']:
        try:
            cp=subprocess.run([sys.executable,'-c',CHILD,str(p),case],text=True,capture_output=True,timeout=35)
            rec['cases'][case]=json.loads(cp.stdout) if cp.returncode==0 else {'err':(cp.stderr or cp.stdout)[-500:]}
        except Exception as e: rec['cases'][case]={'err':repr(e)}
        print(' ',case,rec['cases'][case],flush=True)
    report.append(rec)
Path('runs/night_20260526/round06_cross_repo_solver_scan.json').write_text(json.dumps(report,indent=2,sort_keys=True))
# print top by official_like if available
ok=[r for r in report if isinstance(r['cases'].get('official_like'),dict) and r['cases']['official_like'].get('cost')]
ok.sort(key=lambda r:r['cases']['official_like']['cost'])
print('TOP_OFFICIAL_LIKE')
for r in ok[:20]: print(r['cases']['official_like']['cost'],r['sha'][:8],r['size'],r['path'])
