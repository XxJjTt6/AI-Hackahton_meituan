#!/usr/bin/env python3
# Try company-profit inspired objective: maximize expected completed score minus small courier effort, not avg cost.
import sys,itertools,time,hashlib
from pathlib import Path
sys.path.insert(0,'.'); sys.path.insert(0,'runs')
import solver, proxy_eval
text=Path(sys.argv[1] if len(sys.argv)>1 else 'runs/official_calibrated_low_synth.txt').read_text(); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
by={t:[] for t in tasks}
for r in rows:
    if len(r[1])==1: by[r[1][0]].append(r)
# group score: expected delivered score under at least one accepts, approximate by same subset avg expected_score rather than penalty cost.
def exp_score(rs):
    if not rs: return 0
    ans=0.0
    n=len(rs)
    for mask in range(1,1<<n):
        p=1.0; s=0; cnt=0
        for i,r in enumerate(rs):
            if mask>>i&1: p*=r[4]; s+=r[3]; cnt+=1
            else: p*=1-r[4]
        ans += p*(s/cnt)
    return ans
opts={}
for t in tasks:
    arr=[]; rs=sorted(by[t],key=lambda r:(-r[4],r[3]))[:20]
    for k in [1,2,3]:
        for comb in itertools.combinations(rs,k):
            cs=[r[2] for r in comb]
            if len(cs)!=len(set(cs)): continue
            # profit: delivered score + reliability bonus - courier opportunity cost
            p=1
            for r in comb:p*=1-r[4]
            complete=1-p
            val=exp_score(comb)+12*complete-0.4*k
            arr.append((val,comb))
    opts[t]=sorted(arr,key=lambda x:x[0],reverse=True)[:35]
# Beam maximize profit, then evaluate official cost
states={(frozenset(),):(0.0,())}
states={(0,):(0.0,())}
for t in sorted(tasks):
    ns={}
    for (mask,), (val,path) in states.items():
        for v,comb in [(0,())]+opts[t]:
            cm=0; ok=True
            for r in comb:
                idx=int(r[2][1:]) if r[2].startswith('C') else hash(r[2])%200
                bit=1<<idx
                if cm&bit or mask&bit: ok=False; break
                cm|=bit
            if not ok: continue
            key=(mask|cm,); nv=val+v
            if nv>ns.get(key,(-1,None))[0]: ns[key]=(nv,path+((t,tuple(r[2] for r in comb)),))
    states=dict(sorted(ns.items(),key=lambda kv:kv[1][0],reverse=True)[:800])
best=max(states.values(),key=lambda x:x[0])[1]
res=[(t,list(cs)) for t,cs in best]
base=solver.solve(text)
print('base cost',round(solver._solution_expected_cost(base,rows,T),6),'profit_res cost',round(solver._solution_expected_cost(res,rows,T),6),'n',len(res),'k',{j:sum(len(cs)==j for _,cs in res) for j in range(1,5)})
print('sig',hashlib.sha256(str(res).encode()).hexdigest()[:12]); print(res[:10])
