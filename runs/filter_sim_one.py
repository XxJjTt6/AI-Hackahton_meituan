import sys,collections,time
sys.path.insert(0,'.')
import solver
from pathlib import Path
text=Path('Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt').read_text()
h,*rows=text.strip().splitlines()
for wthr,sthr in [(0.08,55),(0.12,55),(0.08,70)]:
    keep=[h]
    for line in rows:
        k,c,sc,w=line.split('\t')[:4]; sc=float(sc); w=float(w)
        if w<wthr and sc>sthr: continue
        keep.append(line)
    t='\n'.join(keep)+'\n'; t0=time.monotonic(); out=solver.solve(t); dt=time.monotonic()-t0
    parsed=[]; tasks=set()
    for i,line in enumerate(keep[1:]):
        k,c,sc,w=line.split('\t')[:4]; ts=tuple(k.split(',')); parsed.append((k,ts,c,float(sc),float(w),i)); tasks.update(ts)
    print('filter',wthr,sthr,'rows',len(keep)-1,'time',round(dt,2),'cost',round(solver._solution_expected_cost(out,parsed,tasks),2),'shape',sorted(collections.Counter(len(x[1]) for x in out).items()))
