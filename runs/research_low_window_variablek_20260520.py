#!/usr/bin/env python3
import importlib.util,pathlib,itertools,collections,random,argparse,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solver_mod',ROOT/'solver.py')
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse(path):
    text=open(path).read(); lines=text.strip().splitlines(); off=1 if lines and lines[0].startswith('task') else 0
    C=[]; B=set()
    for idx,line in enumerate(lines[off:]):
        p=line.split('\t')
        if len(p)>=4:
            tk,cid,cost,prob=p[:4]; tasks=tuple(x for x in tk.split(',') if x)
            C.append((tk,tasks,cid,float(cost),float(prob),idx)); B.update(tasks)
    return text,C,B

def fmt(sel):
    return [(t,[r[2] for r in sorted(rows,key=lambda r:(r[3],-r[4],r[5]))]) for t,rows in sorted(sel.items())]

def build_opts(C,B,top=18,keep=90):
    by={t:[] for t in B}
    for r in s._canonical_candidates(C):
        if len(r[1])==1 and r[1][0] in by: by[r[1][0]].append(r)
    opts={}
    for t,rows in by.items():
        seed={r[2]:r for r in sorted(rows,key=lambda r:(s._single_expected_cost(r),r[3],-r[4],r[5]))[:top]}
        for r in sorted(rows,key=lambda r:(-r[4],r[3],r[5]))[:top//2]: seed.setdefault(r[2],r)
        rows=list(seed.values()); cur=[]
        for k in (1,2,3):
            if k>len(rows): continue
            for comb in itertools.combinations(rows,k):
                cs=tuple(r[2] for r in comb)
                if len(set(cs))<k: continue
                cost=s._group_expected_cost(comb,1)
                if cost<100-1e-9: cur.append((cost,cs,tuple(comb)))
        cur.sort(key=lambda x:(x[0],len(x[1])))
        opts[t]=cur[:keep]
    return opts

def optimize(sel,C,B,opts,deadline):
    best={t:tuple(rows) for t,rows in sel.items()}; best_cost=sum(s._group_expected_cost(rows,1) for rows in best.values())
    tasks=sorted(best); rng=random.Random(501)
    improved=0; checked=0
    sizes=[2,3,4,5]
    while time.monotonic()<deadline:
        any_imp=False
        windows=[]
        for sz in sizes:
            if sz<=3:
                windows.extend(itertools.combinations(tasks,sz))
            else:
                for _ in range(90): windows.append(tuple(rng.sample(tasks,sz)))
        rng.shuffle(windows)
        for W in windows:
            if time.monotonic()>deadline: break
            W=set(W); outside={r[2] for t,rs in best.items() if t not in W for r in rs}
            old=sum(s._group_expected_cost(best[t],1) for t in W)
            local=[]
            for t in W:
                local.append((t,[o for o in opts[t] if not (set(o[1])&outside)]))
                if not local[-1][1]: break
            if len(local)!=len(W): continue
            # order constrained tasks first
            local.sort(key=lambda x:len(x[1]))
            cur=[]; used=set(); loc_best=None; loc_cost=old
            def dfs(i,cost):
                nonlocal loc_best,loc_cost,checked
                checked+=1
                if cost>=loc_cost-1e-9: return
                if i==len(local): loc_best=list(cur); loc_cost=cost; return
                t,os=local[i]
                for ocost,cs,rows in os[:55]:
                    if set(cs)&used: continue
                    used.update(cs); cur.append((t,rows,ocost)); dfs(i+1,cost+ocost); cur.pop(); used.difference_update(cs)
            dfs(0,0.0)
            if loc_best and loc_cost<old-1e-9:
                for t,rows,cost in loc_best: best[t]=rows
                best_cost+=loc_cost-old; improved+=1; any_imp=True
                print('improve',improved,'win',len(W),'delta',loc_cost-old,'cost',best_cost,'k',collections.Counter(len(v) for v in best.values()),flush=True)
        if not any_imp: break
    return fmt(best),best_cost,improved,checked

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--seconds',type=float,default=50); args=ap.parse_args()
    text,C,B=parse(args.input); base=s.solve(text); row={(r[0],r[2]):r for r in C}; sel=s._result_to_selected(base,row)
    basecost=s._solution_expected_cost(base,C,B); print('base',basecost,'k',collections.Counter(len(x[1]) for x in base),flush=True)
    opts=build_opts(C,B); print('opts',sum(len(v) for v in opts.values()),min(len(v) for v in opts.values()),max(len(v) for v in opts.values()),flush=True)
    out,cost,imp,chk=optimize(sel,C,B,opts,time.monotonic()+args.seconds)
    real=s._solution_expected_cost(out,C,B)
    print('final',real,'delta',real-basecost,'improvements',imp,'checked',chk,'k',collections.Counter(len(x[1]) for x in out),'used',len({c for _,cs in out for c in cs}))
    if real<basecost-1e-9:
        for x in out: print(x)
if __name__=='__main__': main()
