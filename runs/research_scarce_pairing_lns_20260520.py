#!/usr/bin/env python3
import importlib.util,pathlib,sys,random,time,itertools,argparse
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solver_mod',ROOT/'solver.py')
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
sys.path.insert(0,str(ROOT/'runs')); import proxy_eval

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--seconds',type=float,default=20); args=ap.parse_args()
    text=proxy_eval.make_scarce(); C,tasks,couriers=proxy_eval.parse(text); B=set(tasks); deadline=time.monotonic()+args.seconds
    base=s.solve(text); basecost=s._solution_expected_cost(base,C,B); row={(r[0],r[2]):r for r in C}; base_sel=s._result_to_selected(base,row)
    base_cov={t for rows in base_sel.values() for t in rows[0][1]}
    print('base',basecost,'groups',len(base),'cov',len(base_cov),'sig',hash(tuple((k,tuple(v)) for k,v in base)))
    # Build all single-courier columns up to pair task keys among base covered tasks; search exact partition of a random window.
    all_rows=s._canonical_candidates(C); rng=random.Random(20260520)
    best=base; bestcost=basecost
    selected=base_sel
    groups=list(selected.keys())
    for it in range(200):
        if time.monotonic()>deadline: break
        # choose 5-10 groups, replace tasks inside with any rows whose task set subset equals window tasks, preserving courier uniqueness outside.
        seed=rng.choice(groups); window=set(selected[seed][0][1])
        while len(window)<rng.randint(8,14):
            g=rng.choice(groups); window.update(selected[g][0][1])
            if len(window)>16: break
        outside=[]; outside_c=set(); outside_t=set()
        for k,cs in best:
            rr=[row[(k,c)] for c in cs if (k,c) in row]
            if not rr or set(rr[0][1]) & window: continue
            outside.append((k,cs)); outside_c.update(cs); outside_t.update(rr[0][1])
        cand_rows=[]
        for r in all_rows:
            if r[2] in outside_c: continue
            if set(r[1]) and set(r[1])<=window and len(r[1])<=2:
                cost=s._group_expected_cost([r],len(r[1]));
                if cost<100*len(r[1]): cand_rows.append((cost,r))
        # DP exact cover window tasks with no courier reuse, allow one uncovered only if base window had one uncovered.
        wtasks=sorted(window); tid={t:i for i,t in enumerate(wtasks)}; target=(1<<len(wtasks))-1
        states={(0,frozenset()):(0.0,())}
        for cost,r in sorted(cand_rows,key=lambda x:x[0]-100*len(x[1][1]))[:500]:
            tm=0
            for t in r[1]: tm|=1<<tid[t]
            cm=frozenset([r[2]])
            new=dict(states)
            for (mask,used),(val,path) in states.items():
                if mask&tm or r[2] in used: continue
                key=(mask|tm,used|cm); nv=val+cost; old=new.get(key)
                if old is None or nv<old[0]: new[key]=(nv,path+(r,))
            if len(new)>4000:
                new=dict(sorted(new.items(),key=lambda kv:kv[1][0]+100*(len(wtasks)-bin(kv[0][0]).count('1')))[:4000])
            states=new
        best_local=None
        for (mask,used),(val,path) in states.items():
            total=val+100*(len(wtasks)-bin(mask).count('1'))
            if best_local is None or total<best_local[0]: best_local=(total,path,mask)
        if not best_local: continue
        new_out=outside+[(r[0],[r[2]]) for r in best_local[1]]
        cost=s._solution_expected_cost(new_out,C,B); cov=s._solution_covered_count(new_out,C)
        if cost<bestcost-1e-9 and cov>=s._solution_covered_count(best,C):
            best=new_out; bestcost=cost; selected=s._result_to_selected(best,row); groups=list(selected.keys())
            print('IMPROVE',it,bestcost,bestcost-basecost,'cov',cov,'window',len(window),flush=True)
    print('done best',bestcost,bestcost-basecost,'cov',s._solution_covered_count(best,C),'groups',len(best))
if __name__=='__main__': main()
