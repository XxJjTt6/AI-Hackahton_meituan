#!/usr/bin/env python3
import argparse, collections, importlib.util, itertools, pathlib, time, random, math
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solver_mod',ROOT/'solver.py')
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse_file(path):
    text=pathlib.Path(path).read_text(); lines=text.strip().splitlines(); off=1 if lines and lines[0].startswith('task') else 0
    C=[]; B=set()
    for i,line in enumerate(lines[off:]):
        p=line.split('\t')
        if len(p)<4: continue
        tk,c,sc,w=p[:4]; ts=tuple(x for x in tk.split(',') if x)
        C.append((tk,ts,c,float(sc),float(w),i)); B.update(ts)
    return text,C,B

def masks_for(C,B):
    tasks=sorted(B); couriers=sorted({r[2] for r in C})
    ti={t:i for i,t in enumerate(tasks)}; ci={c:i for i,c in enumerate(couriers)}
    return tasks,couriers,ti,ci

def result_to_cols(out,C,B,ti,ci):
    row={(r[0],r[2]):r for r in C}; cols=[]
    for k,cs in out:
        rows=[row.get((k,c)) for c in cs]; rows=[r for r in rows if r]
        if not rows: continue
        tm=0; cm=0
        for t in rows[0][1]: tm|=1<<ti[t]
        for r in rows: cm|=1<<ci[r[2]]
        cost=s._group_expected_cost(rows,len(rows[0][1]))
        cols.append((cost,tm,cm,k,tuple(r[2] for r in rows),tuple(rows),'base'))
    return cols

def build_single_task_columns(C,B,ti,ci,top=18,keep=90,dual=None):
    by={t:[] for t in B}
    for r in s._canonical_candidates(C):
        if len(r[1])==1 and r[1][0] in by: by[r[1][0]].append(r)
    cols=[]
    dual=dual or {}
    for t,rows in by.items():
        seed={r[2]:r for r in sorted(rows,key=lambda r:(s._single_expected_cost(r)+dual.get(r[2],0), r[3], -r[4], r[5]))[:top]}
        for r in sorted(rows,key=lambda r:(-r[4], r[3], r[5]))[:max(8,top//2)]: seed.setdefault(r[2],r)
        rows=list(seed.values()); opts=[]
        for k in (1,2,3):
            if k>len(rows): continue
            for comb in itertools.combinations(rows,k):
                cs=tuple(r[2] for r in comb)
                if len(cs)!=len(set(cs)): continue
                cost=s._group_expected_cost(comb,1)
                adj=cost+sum(dual.get(c,0) for c in cs)
                if cost<100-1e-9: opts.append((adj,cost,cs,comb))
        opts.sort(key=lambda x:(x[0],x[1],len(x[2])))
        for adj,cost,cs,comb in opts[:keep]:
            tm=1<<ti[t]; cm=0
            for c in cs: cm|=1<<ci[c]
            cols.append((cost,tm,cm,t,cs,tuple(comb),'single'))
    return cols

def build_bundle_columns(C,B,ti,ci,top_per_key=8,keep_per_key=8):
    grouped=collections.defaultdict(list)
    for r in s._canonical_candidates(C):
        if len(r[1])>=2 and all(t in ti for t in r[1]): grouped[r[0]].append(r)
    cols=[]
    for k,rows in grouped.items():
        rows=sorted(rows,key=lambda r:(_group_cost_one(r),-r[4],r[5]))[:top_per_key]
        opts=[]; task_count=len(rows[0][1]) if rows else 0
        for kk in (1,2,3):
            if kk>len(rows): continue
            for comb in itertools.combinations(rows,kk):
                cs=tuple(r[2] for r in comb)
                if len(cs)!=len(set(cs)): continue
                cost=s._group_expected_cost(comb,task_count)
                if cost<100*task_count-1e-9: opts.append((cost,cs,comb))
        opts.sort(key=lambda x:(x[0],len(x[1])))
        tm=0
        for t in rows[0][1] if rows else (): tm|=1<<ti[t]
        for cost,cs,comb in opts[:keep_per_key]:
            cm=0
            for c in cs: cm|=1<<ci[c]
            cols.append((cost,tm,cm,k,cs,tuple(comb),'bundle'))
    return cols

def _group_cost_one(r): return s._group_expected_cost([r],len(r[1]))

def beam_master(cols,n_tasks,incumbent_cost,deadline,beam=90000,keep_cov=True):
    full=(1<<n_tasks)-1
    cols=sorted(cols,key=lambda x:(x[0]-100*x[1].bit_count(),x[0]))
    states={(0,0):(0.0,())}; best=(incumbent_cost,None)
    for idx,col in enumerate(cols):
        if time.monotonic()>deadline: break
        cost,tm,cm,*rest=col
        new=dict(states)
        for (tmask,cmask),(val,path) in list(states.items()):
            if tmask&tm or cmask&cm: continue
            nv=val+cost; nt=tmask|tm; nc=cmask|cm
            # incumbent pruning with penalty lower bound
            obj=nv+100*(n_tasks-nt.bit_count())
            if obj>incumbent_cost+5: continue
            old=new.get((nt,nc))
            if old is None or nv<old[0]-1e-9: new[(nt,nc)]=(nv,path+(idx,))
        if len(new)>beam:
            items=sorted(new.items(),key=lambda kv:(kv[1][0]+100*(n_tasks-kv[0][0].bit_count()),-kv[0][0].bit_count(),kv[1][0]))[:beam]
            new=dict(items)
        states=new
    for (tm,cm),(val,path) in states.items():
        obj=val+100*(n_tasks-tm.bit_count())
        if obj<best[0]-1e-9:
            best=(obj,path)
    return best

def cols_to_out(cols,path):
    if path is None: return None
    out=[]
    for idx in path:
        cost,tm,cm,k,cs,rows,src=cols[idx]
        out.append((k,list(cs)))
    return sorted(out,key=lambda x:x[0])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--mode',choices=['single','bundle','both'],default='both'); ap.add_argument('--seconds',type=float,default=60); ap.add_argument('--beam',type=int,default=90000)
    args=ap.parse_args(); text,C,B=parse_file(args.input); tasks,couriers,ti,ci=masks_for(C,B)
    base=s.solve(text); basecost=s._solution_expected_cost(base,C,B); basecols=result_to_cols(base,C,B,ti,ci)
    print('base',basecost,'groups',len(base),'k',collections.Counter(len(x[1]) for x in base),'task_groups',collections.Counter(len(x[0].split(',')) for x in base),flush=True)
    cols=list(basecols)
    if args.mode in ('single','both'):
        for seed in range(4):
            dual={c:(seed-1.5)*0.08 for c in couriers}
            cols.extend(build_single_task_columns(C,B,ti,ci,top=12+seed*2,keep=36,dual=dual))
    if args.mode in ('bundle','both'):
        cols.extend(build_bundle_columns(C,B,ti,ci,top_per_key=9,keep_per_key=6))
    # de-dup by masks+couriers keep min cost
    d={}
    for col in cols:
        key=(col[1],col[2],col[3],col[4])
        if key not in d or col[0]<d[key][0]: d[key]=col
    cols=list(d.values())
    print('cols',len(cols),'basecols',len(basecols),'single',sum(1 for c in cols if c[-1]=='single'),'bundle',sum(1 for c in cols if c[-1]=='bundle'),flush=True)
    obj,path=beam_master(cols,len(tasks),basecost,time.monotonic()+args.seconds,beam=args.beam)
    out=cols_to_out(cols,path)
    print('best_obj',obj,'delta',obj-basecost,'path',None if path is None else len(path),flush=True)
    if out:
        real=s._solution_expected_cost(out,C,B)
        print('real',real,'covered',s._solution_covered_count(out,C),'k',collections.Counter(len(x[1]) for x in out),'task_groups',collections.Counter(len(x[0].split(',')) for x in out),'used',len({c for _,cs in out for c in cs}))
        if real<basecost-1e-9:
            for x in out: print(x)
if __name__=='__main__': main()
