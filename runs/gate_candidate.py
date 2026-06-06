#!/usr/bin/env python3
import sys,subprocess,json,re,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=sys.argv[1]
cmd=[sys.executable,'runs/proxy_eval.py','solver.py',p]
r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=160)
print(r.stdout)
if r.returncode: print(r.stderr); sys.exit(r.returncode)
# Conservative: parse candidate rows and reject if large/low worsen or scarce gain <20 proxy points.
blocks=r.stdout.split('solver ')
if len(blocks)<3: sys.exit(2)
base=blocks[1]; cand=blocks[2]
def parse(block):
 d={}
 for line in block.splitlines():
  m=re.search(r'\s+(large|low025|low030|scarce40)\s+.*cost=\s*([0-9.]+).*cov=(\d+)/(\d+)',line)
  if m:d[m.group(1)]=(float(m.group(2)),int(m.group(3)),int(m.group(4)))
 return d
B=parse(base); C=parse(cand); print('parsed',B,C)
fail=[]
for k in ['large','low025','low030']:
 if k in B and k in C and C[k][0]>B[k][0]+1e-6: fail.append(f'{k} worsens {B[k][0]}->{C[k][0]}')
if 'scarce40' in B and 'scarce40' in C and B['scarce40'][0]-C['scarce40'][0]<20: fail.append('scarce proxy gain <20')
if fail:
 print('REJECT',fail); sys.exit(1)
print('PASS strong proxy gate')
