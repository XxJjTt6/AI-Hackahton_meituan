#!/usr/bin/env python3
import importlib.util,pathlib,itertools,argparse,math,time,collections
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
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--top',type=int,default=22); ap.add_argument('--opts',type=int,default=120); ap.add_argument('--beam',type=int,default=120000)
    args=ap.parse_args(); text=open(args.input).read(); C,B=parse(text)
    base=s.solve(text); basecost=s._solution_expected_cost(base,C,B); print('base',basecost)
    tasks=sorted(B); couriers=sorted({r[2] for r in C}); cid={c:i for i,c in enumerate(couriers)}
    by={t:[] for t in tasks}
    for r in s._canonical_candidates(C):
        if len(r[1])==1: by[r[1][0]].append(r)
    options=[]
    for t in tasks:
        rows=sorted(by[t],key=lambda r:s._single_expected_cost(r))[:args.top]
        opts=[]
        for k in [1,2,3]:
            for comb in itertools.combinations(rows,k):
                if len({r[2] for r in comb})<k: continue
                cost=s._group_expected_cost(comb,1); mask=0
                for r in comb: mask|=1<<cid[r[2]]
                opts.append((cost,mask,tuple(r[2] for r in comb)))
        opts=sorted(opts,key=lambda x:x[0])[:args.opts]
        options.append((t,opts))
    states={0:(0.0,())}
    for ti,(t,opts) in enumerate(options):
        new={}
        for used,(val,path) in states.items():
            for cost,mask,cs in opts:
                if used&mask: continue
                nu=used|mask; nv=val+cost
                old=new.get(nu)
                if old is None or nv<old[0]: new[nu]=(nv,path+((t,cs),))
        if len(new)>args.beam:
            # prefer low total and exactly around 2 riders per task so far
            target=2*(ti+1)
            new=dict(sorted(new.items(),key=lambda kv:(kv[1][0]+0.02*abs(kv[0].bit_count()-target),kv[1][0]))[:args.beam])
        states=new
        print('task',ti+1,'states',len(states),'best',min(v[0] for v in states.values()) if states else None,flush=True)
        if not states: break
    best=min(states.values(),key=lambda x:x[0]) if states else None
    if best:
        out=[(t,list(cs)) for t,cs in best[1]]; cost=s._solution_expected_cost(out,C,B); print('best',cost,'delta',cost-basecost,'k',collections.Counter(len(cs) for t,cs in out),'used',len({c for t,cs in out for c in cs}))
        print(out[:10])
if __name__=='__main__': main()
