import sys
sys.path.insert(0,".")
import solver
from pathlib import Path
text=Path('Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt').read_text()
lines=text.strip().splitlines(); hdr=lines[0]; rows=lines[1:]
for wthr in [0.03,0.05,0.08,0.10,0.12]:
  for sthr in [40,55,70,85]:
    keep=[hdr]
    for line in rows:
      k,c,sc,w=line.split('\t')[:4]
      sc=float(sc); w=float(w)
      if w<wthr and sc>sthr: continue
      keep.append(line)
    t='\n'.join(keep)+'\n'
    out=solver.solve(t)
    parsed=[]; tasks=set()
    for i,line in enumerate(keep[1:]):
      k,c,sc,w=line.split('\t')[:4]; ts=tuple(k.split(',')); parsed.append((k,ts,c,float(sc),float(w),i)); tasks.update(ts)
    cost=solver._solution_expected_cost(out,parsed,tasks)
    print('w',wthr,'s',sthr,'rows',len(keep)-1,'cost',round(cost,2),'groups',len(out),'shape',sorted(__import__('collections').Counter(len(x[1]) for x in out).items()))
