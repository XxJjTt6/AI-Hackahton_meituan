#!/usr/bin/env python3
# Explore alternative 39-task scarce pairings on public scarce proxy with current coverage pattern.
import sys,itertools,time
from pathlib import Path
sys.path.insert(0,'.'); sys.path.insert(0,'runs')
import solver, proxy_eval
text=proxy_eval.make_scarce(); rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
# Current official seed401 cache pairs; use same covered set/missing T0033 when possible on public proxy.
cur=[('T0000,T0027',['C005']),('T0001,T0035',['C018']),('T0002,T0038',['C009']),('T0003,T0024',['C012']),('T0004,T0018',['C007']),('T0005,T0036',['C019']),('T0006,T0030',['C003']),('T0007,T0008',['C001']),('T0009,T0011',['C014']),('T0010,T0029',['C004']),('T0012,T0019',['C010']),('T0013,T0039',['C013']),('T0014,T0031',['C008']),('T0015,T0034',['C015']),('T0016',['C000']),('T0017,T0032',['C002']),('T0020,T0023',['C016']),('T0021,T0026',['C017']),('T0022,T0037',['C011']),('T0025,T0028',['C006'])]
covered=set(t for k,cs in cur for t in k.split(',')); missing=T-covered
print('public tasks',len(T),'cache missing',sorted(missing))
lut={(r[0],r[2]):r for r in rows}
def rc(sol): return solver._solution_expected_cost(sol,rows,T)
print('cache cost on public',round(rc(cur),6))
# Build all positive single-courier bundles among covered tasks only, plus single T0016 preference.
covered=sorted(covered); ti={t:i for i,t in enumerate(covered)}; ci={c:i for i,c in enumerate(couriers)}
items=[]
for r in rows:
    if r[2] not in ci: continue
    if all(t in ti for t in r[1]) and 1<=len(r[1])<=2:
        c=solver._group_expected_cost([r],len(r[1])); gain=100*len(r[1])-c
        if gain>0:
            tm=sum(1<<ti[t] for t in r[1]); cm=1<<ci[r[2]]; items.append((gain,c,tm,cm,r[0],r[2],r[1]))
# force T0016 single? score both.
def beam(force_t0016=True):
    states={(0,0):(0.0,())}
    for gain,c,tm,cm,k,cid,ts in sorted(items, reverse=True):
        if force_t0016 and ('T0016' in ts and (k!='T0016' or cid!='C000')): continue
        if force_t0016 and ('T0016' not in ts and cid=='C000'): pass
        ns=dict(states)
        for (m,u),(g,path) in list(states.items()):
            if m&tm or u&cm: continue
            key=(m|tm,u|cm); val=g+gain
            if val>ns.get(key,(-1,None))[0]: ns[key]=(val,path+((k,cid,c),))
        if len(ns)>800:
            states=dict(sorted(ns.items(),key=lambda kv:(kv[1][0]+20*bin(kv[0][0]).count('1'),kv[1][0]),reverse=True)[:800])
        else: states=ns
    best=max(states.items(),key=lambda kv: kv[1][0])
    gain,path=best[1]; score=100*len(T)-gain # includes penalty for uncovered public T0033 maybe if not covered mask
    return score,path,bin(best[0][0]).count('1')
for f in [True,False]:
    score,path,cov=beam(f); print('beam force',f,'score',round(score,4),'covered_in_cache_set',cov,'groups',len(path))
    print(path[:25])
