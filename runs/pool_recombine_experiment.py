#!/usr/bin/env python3
# Prototype external experiment: run solver variants as black-box solutions and recombine groups as set packing.
import sys, time, importlib.util, itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval

def load(path):
    spec=importlib.util.spec_from_file_location('m'+str(abs(hash(path))), str(ROOT/path)); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def recombine(mod, sols, rows, tasks, deadline):
    lut={(r[0],r[2]):r for r in rows}; tid={t:i for i,t in enumerate(sorted(tasks))}; cid={c:i for i,c in enumerate(sorted({r[2] for r in rows}))}
    cols=[]; seen=set()
    for sol in sols:
        for k,cs in sol:
            rr=[]; tm=0; cm=0; ok=True
            for c in cs:
                r=lut.get((k,c))
                if not r: ok=False; break
                rr.append(r); cm |= 1<<cid[c]
            if not ok or not rr: continue
            for t in rr[0][1]: tm |= 1<<tid[t]
            key=(tm,cm,k,tuple(cs))
            if key in seen: continue
            seen.add(key); cost=mod._group_expected_cost(rr,len(rr[0][1])); gain=100*len(rr[0][1])-cost
            if gain>1e-9: cols.append((gain,cost,tm,cm,k,tuple(cs)))
    cols.sort(reverse=True)
    # beam set packing by gain
    states={(0,0):(0,())}
    for idx,col in enumerate(cols[:250]):
        if time.monotonic()>deadline: break
        gain,cost,tm,cm,k,cs=col; add=[]
        for (tmask,cmask),(val,chosen) in list(states.items()):
            if tmask&tm or cmask&cm: continue
            nk=(tmask|tm, cmask|cm); nv=val+gain
            if nk not in states or nv>states[nk][0]: add.append((nk,(nv,chosen+(idx,))))
        for k2,v in add: states[k2]=v
        if len(states)>3000: states=dict(sorted(states.items(), key=lambda kv:(kv[1][0], bin(kv[0][0]).count('1')), reverse=True)[:1200])
    best=max(states.items(), key=lambda kv:(kv[1][0], bin(kv[0][0]).count('1')))[1][1]
    return [(cols[i][4], list(cols[i][5])) for i in best]

def main():
    mods=[load('solver.py'), load('runs/low_pair_exchange_bigger.py'), load('runs/low_picker_min_guard.py')]
    for name,text in [('low025',proxy_eval.make_low(.25)),('low030',proxy_eval.make_low(.30)),('scarce40',proxy_eval.make_scarce())]:
        rows,tasks,c=proxy_eval.parse(text); T=set(tasks); sols=[]
        for m in mods:
            sols.append(m.solve(text))
        base=mods[0]._solution_expected_cost(sols[0],rows,T)
        rec=recombine(mods[0], sols, rows, T, time.monotonic()+1.0)
        rc=mods[0]._solution_expected_cost(rec, rows, T)
        print(name,'base',round(base,2),'recombine',round(rc,2),'groups',len(rec))
if __name__=='__main__': main()
