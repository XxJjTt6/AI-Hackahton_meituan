#!/usr/bin/env python3
import subprocess, sys, time, datetime as dt
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
experiments=[
    ('gate_safe_best',[sys.executable,'runs/gate_candidate.py','solver.py']),
    ('feature_summary',[sys.executable,'runs/input_feature_summary.py']),
]
print('[loop] foreground iteration heartbeat start', dt.datetime.now().isoformat(timespec='seconds'), flush=True)
for i,(name,cmd) in enumerate(experiments,1):
    print(f'[loop] step {i}/{len(experiments)} {name}: hypothesis=diagnose stability/features before next refactor', flush=True)
    p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
    print(p.stdout[-4000:], flush=True)
    print(f'[loop] step {name} done rc={p.returncode}', flush=True)
print('[loop] done; next manual experiment needed', flush=True)
