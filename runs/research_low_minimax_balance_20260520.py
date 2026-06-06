#!/usr/bin/env python3
import importlib.util,pathlib,itertools,math,argparse
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solver_mod',ROOT/'solver.py')
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse(text):
    lines=text.strip().splitlines(); off=1 if lines and lines[0].startswith('task') else 0
    C=[]; B=set()
    for idx,line in enumerate(lines[off:]):
        p=line.strip().split('\t')
        if len(p)<4: continue
        tk,cid,cost,prob=p[:4]; tasks=tuple(x.strip() for x in tk.split(',') if x.strip())
        C.append((tk,tasks,cid,float(cost),float(prob),idx)); B.update(tasks)
    return C,B

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); args=ap.parse_args()
    text=open(args.input).read(); C,B=parse(text); base=s.solve(text); basecost=s._solution_expected_cost(base,C,B)
    row={(r[0],r[2]):r for r in C}; base_sel=s._result_to_selected(base,row)
    base_max=max(s._group_expected_cost(rows,1) for rows in base_sel.values())
    print('base sum',basecost,'max_group',base_max)
    tasks=sorted(B); couriers=sorted({r[2] for r in C}); cidx={c:i for i,c in enumerate(couriers)}
    by={t:[] for t in tasks}
    for r in s._canonical_candidates([x for x in C if len(x[1])==1]): by[r[1][0]].append(r)
    for t in tasks: by[t].sort(key=lambda r:s._single_expected_cost(r)); by[t]=by[t][:28]
    pair_opts=[]
    for t in tasks:
        opts=[]
        for a,b in itertools.combinations(by[t],2):
            if a[2]==b[2]: continue
            cost=s._group_expected_cost([a,b],1); mask=(1<<cidx[a[2]])|(1<<cidx[b[2]])
            opts.append((cost,mask,(a,b)))
        opts.sort(key=lambda x:(x[0],-min(x[2][0][4],x[2][1][4])))
        pair_opts.append((t,opts[:120]))
    # Binary threshold feasibility, then within threshold minimize sum.
    for slack in [0,1,2,3,5,8,12,20]:
        limit=base_max+slack
        states={0:(0.0,())}
        ok=True
        for t,opts in pair_opts:
            new={}
            allowed=[o for o in opts if o[0]<=limit]
            for used,(val,path) in states.items():
                for cost,mask,pair in allowed:
                    if used&mask: continue
                    nu=used|mask; nv=val+cost
                    old=new.get(nu)
                    if old is None or nv<old[0]: new[nu]=(nv,path+((t,pair),))
            if len(new)>20000: new=dict(sorted(new.items(),key=lambda kv:kv[1][0])[:20000])
            states=new
            if not states: ok=False; break
        if not ok:
            print('slack',slack,'infeasible'); continue
        best=min(states.values(),key=lambda x:x[0])
        out=[(t,[a[2],b[2]]) for t,(a,b) in best[1]]
        cost=s._solution_expected_cost(out,C,B); mx=max(s._group_expected_cost([row[(t,c)] for c in cs],1) for t,cs in out)
        print('slack',slack,'sum',cost,'delta',cost-basecost,'max',mx,'groups',len(out))
if __name__=='__main__': main()
