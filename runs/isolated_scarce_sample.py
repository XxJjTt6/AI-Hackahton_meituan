#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
script='''
import sys,time,hashlib
from pathlib import Path
ROOT=Path(sys.argv[1]); p=sys.argv[2]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
mod=proxy_eval.load(ROOT/p); text=proxy_eval.make_scarce(); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
t0=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t0
lut={(r[0],r[2]):r for r in rows}; cov=set()
for k,cs in out:
    for c in cs:
        r=lut.get((k,c))
        if r: cov.update(r[1]); break
sig=hashlib.sha256('\\n'.join(f'{k}:{",".join(cs)}' for k,cs in out).encode()).hexdigest()[:12]
print(round(mod._solution_expected_cost(out,rows,T),6),round(dt,3),len(cov),len(out),sig)
'''
for p in sys.argv[1:]:
    print('##',p,flush=True)
    for i in range(6):
        r=subprocess.run([sys.executable,'-c',script,str(ROOT),p],text=True,capture_output=True,timeout=25)
        print(i+1, r.stdout.strip() or r.stderr.strip(), flush=True)
