#!/usr/bin/env python3
from pathlib import Path
import subprocess, re, tempfile, shutil, os, sys
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
base=(ROOT/'solver.py').read_text()
variants=[]
repls=[
('time8.55','A=i+8.7','A=i+8.55'),('time8.8','A=i+8.7','A=i+8.8'),
('low_deep_1.0','min(A,time.monotonic()+1.2))\n\tif J and time.monotonic()<A-.95:D=_low_late_acceptance','min(A,time.monotonic()+1.0))\n\tif J and time.monotonic()<A-.95:D=_low_late_acceptance'),
('late_0.65','min(A,time.monotonic()+.85))\n\tif J and time.monotonic()<A-.32:D=_shift','min(A,time.monotonic()+.65))\n\tif J and time.monotonic()<A-.32:D=_shift'),
('no_low_shift','\n\tif J and time.monotonic()<A-.32:D=_shift_couriers_between_groups(D,C,B,min(A,time.monotonic()+.24),max_moves=30)',''),
]
outdir=ROOT/'runs'/'knob_scan'; outdir.mkdir(exist_ok=True)
for name,a,b in repls:
    if a not in base:
        print('missing',name); continue
    p=outdir/(name+'.py'); p.write_text(base.replace(a,b,1)); variants.append(p)
print('variants', [p.name for p in variants])
for p in variants:
    print('\n###',p.name, flush=True)
    r=subprocess.run(['python3','runs/fixed_baseline_eval.py',str(p.relative_to(ROOT))],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
    lines=r.stdout.strip().splitlines()
    for ln in lines:
        if any(k in ln for k in ['low025','low030','public_large','MEAN']): print(ln)
