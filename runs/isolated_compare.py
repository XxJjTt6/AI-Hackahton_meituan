#!/usr/bin/env python3
import subprocess,sys,os,json,hashlib,tempfile,textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
script='''
import sys,time,hashlib
from pathlib import Path
ROOT=Path(sys.argv[1]); p=sys.argv[2]; case=sys.argv[3]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
mod=proxy_eval.load(ROOT/p)
if case=='large': text=proxy_eval.DATA.read_text()
elif case=='low025': text=proxy_eval.make_low(.25)
elif case=='low030': text=proxy_eval.make_low(.30)
elif case=='singlelow':
    rows,tasks,couriers=proxy_eval.parse(proxy_eval.DATA.read_text()); keep_t=set(tasks[:30]); keep_c=set(couriers[:60]); out=[]; idx=0
    for key,ts,c,sc,w,i in rows:
        if c in keep_c and len(ts)==1 and ts[0] in keep_t:
            out.append((key,ts,c,sc,max(.0001,min(.999,w*.25)),idx)); idx+=1
    text=proxy_eval.serialize(out)
else: text=proxy_eval.make_scarce()
rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
t0=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t0
sig=hashlib.sha256('\\n'.join(f'{k}:{",".join(cs)}' for k,cs in out).encode()).hexdigest()[:12]
print(case,round(mod._solution_expected_cost(out,rows,T),6),round(dt,3),len(out),sig)
'''
for p in sys.argv[1:]:
    print('##',p,flush=True)
    for case in ['large','low025','low030','singlelow','scarce']:
        for i in range(2):
            r=subprocess.run([sys.executable,'-c',script,str(ROOT),p,case],text=True,capture_output=True,timeout=25)
            print(r.stdout.strip() or r.stderr.strip(),flush=True)
