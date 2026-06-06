#!/usr/bin/env python3
import importlib.util,pathlib,itertools,math
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solver_mod',ROOT/'solver.py')
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
text=open(ROOT/'runs/official_calibrated_low_synth.txt').read()
C=[];B=set(); lines=text.strip().splitlines(); off=1 if lines[0].startswith('task') else 0
for idx,line in enumerate(lines[off:]):
    p=line.split('\t'); tk,c,cost,prob=p[:4]; C.append((tk,tuple(tk.split(',')),c,float(cost),float(prob),idx)); B.update(tk.split(','))
out=s.solve(text); row={(r[0],r[2]):r for r in C}; sel=s._result_to_selected(out,row)
print('selected cost',s._solution_expected_cost(out,C,B),'groups',len(out))
by={t:[] for t in B}
for r in s._canonical_candidates(C):
    if len(r[1])==1: by[r[1][0]].append(r)
for t in sorted(B):
    chosen=sel[t]; chosen_cs=tuple(r[2] for r in chosen); ccost=s._group_expected_cost(chosen,1); cp=1-math.prod(1-r[4] for r in chosen); craw=(ccost-(1-cp)*100)/cp
    opts=[]
    top=sorted(by[t],key=lambda r:s._single_expected_cost(r))[:20]
    for k in [1,2,3]:
        for comb in itertools.combinations(top,k):
            if len({r[2] for r in comb})<k: continue
            cost=s._group_expected_cost(comb,1); p=1-math.prod(1-r[4] for r in comb); raw=(cost-(1-p)*100)/p if p else 999
            opts.append((cost,p,raw,tuple(r[2] for r in comb)))
    opts.sort()
    dominators=[o for o in opts if o[0]<=ccost+1e-9 and o[1]>=cp+1e-9 and set(o[3])!=set(chosen_cs)]
    highp=[o for o in sorted(opts,key=lambda x:(-x[1],x[0]))[:3]]
    print(t,'chosen',chosen_cs,'cost',round(ccost,4),'p',round(cp,4),'raw',round(craw,3),'dom',len(dominators),'best_cost',tuple(round(x,4) if isinstance(x,float) else x for x in opts[0][:3]),opts[0][3],'top_p',[(round(a,2),round(b,3),round(c,2),d) for a,b,c,d in highp])
