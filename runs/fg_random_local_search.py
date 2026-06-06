#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys, time, random
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
base=(ROOT/'solver.py').read_text(); out=ROOT/'runs/fg_random'; out.mkdir(exist_ok=True)
patterns=[
 ('low_global_time_90', 'p=_solve_low_global_column_search(C,B,min(A,time.monotonic()+.75))', 'p=_solve_low_global_column_search(C,B,min(A,time.monotonic()+.90))'),
 ('low_global_time_55', 'p=_solve_low_global_column_search(C,B,min(A,time.monotonic()+.75))', 'p=_solve_low_global_column_search(C,B,min(A,time.monotonic()+.55))'),
 ('low_col_time_60', 's=_solve_low_column_search(W if W else H,B,min(A,time.monotonic()+.45))', 's=_solve_low_column_search(W if W else H,B,min(A,time.monotonic()+.60))'),
 ('scarce_k2_time_80', 'w=_solve_scarce_k2_column_search(C,B,min(A,time.monotonic()+.65))', 'w=_solve_scarce_k2_column_search(C,B,min(A,time.monotonic()+.80))'),
 ('scarce_bundle_time_65', 'x=_solve_scarce_bundle_mcf_enum(C,B,min(A,time.monotonic()+.85))', 'x=_solve_scarce_bundle_mcf_enum(C,B,min(A,time.monotonic()+.65))'),
 ('scarce_group_time_95', 'Z=_solve_scarce_bundle_group_mcf_enum(C,B,min(A,time.monotonic()+.75))', 'Z=_solve_scarce_bundle_group_mcf_enum(C,B,min(A,time.monotonic()+.95))'),
]
for name,a,b in patterns:
    if a not in base:
        print('[missing]',name); continue
    p=out/(name+'.py'); p.write_text(base.replace(a,b)); print('\nCAND',name, flush=True)
    try:
        r=subprocess.run([sys.executable,'_bench.py',str(p),'1'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=35)
        print(r.stdout, flush=True)
        if r.returncode: continue
        r=subprocess.run([sys.executable,'runs/low_single_proxy_eval.py','solver.py',str(p)],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=75)
        print(r.stdout[-1800:], flush=True)
    except subprocess.TimeoutExpired:
        print('TIMEOUT reject', flush=True)
