#!/usr/bin/env python3
import importlib.util, pathlib, itertools, math, random, argparse, time, collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solver_mod',ROOT/'solver.py')
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse(path):
    text=open(path).read(); lines=text.strip().splitlines(); off=1 if lines and lines[0].startswith('task') else 0
    C=[]; B=set()
    for idx,line in enumerate(lines[off:]):
        p=line.split('\t')
        if len(p)<4: continue
        tk,cid,cost,prob=p[:4]; tasks=tuple(x for x in tk.split(',') if x)
        C.append((tk,tasks,cid,float(cost),float(prob),idx)); B.update(tasks)
    return text,C,B

def row_group_cost(rows): return s._group_expected_cost(rows,len(rows[0][1]))

def selected_from_out(out,C):
    row={(r[0],r[2]):r for r in C}; return s._result_to_selected(out,row)

def fmt(sel): return [(t,[r[2] for r in sorted(rows,key=lambda r:(r[3],-r[4],r[5]))]) for t,rows in sorted(sel.items())]

def build_task_options(C,B,prices,top=26,keep=80,ks=(1,2,3)):
    by={t:[] for t in B}
    for r in s._canonical_candidates(C):
        if len(r[1])==1 and r[1][0] in by: by[r[1][0]].append(r)
    opts={}
    for t,rows in by.items():
        # include both cheap and high-p rows so pricing can discover non-current columns
        cand={r[2]:r for r in sorted(rows,key=lambda r:(s._single_expected_cost(r)+prices.get(r[2],0), r[3], -r[4], r[5]))[:top]}
        for r in sorted(rows,key=lambda r:(-r[4], r[3], r[5]))[:max(8,top//2)]: cand.setdefault(r[2],r)
        rows=list(cand.values())
        cur=[]
        for k in ks:
            if k>len(rows): continue
            for comb in itertools.combinations(rows,k):
                cids=tuple(r[2] for r in comb)
                if len(set(cids))<k: continue
                gc=row_group_cost(comb)
                adj=gc+sum(prices.get(c,0) for c in cids)
                cur.append((adj,gc,cids,comb))
        cur.sort(key=lambda x:(x[0],x[1],len(x[2])))
        opts[t]=cur[:keep]
    return opts

def lagrangian(C,B,rounds=140,seed=7):
    base=BASE_OUT
    base_sel=selected_from_out(base,C)
    prices={c:0.0 for c in {r[2] for r in C}}
    best_cols={}
    rng=random.Random(seed)
    for it in range(rounds):
        opts=build_task_options(C,B,prices,top=14+(it%2)*4,keep=32)
        used=collections.Counter(); chosen={}; raw=0.0
        for t in sorted(B, key=lambda x:(it*17+hash(x))%997):
            if not opts.get(t): continue
            # small perturbation avoids same hot-courier trap
            item=min(opts[t][:20], key=lambda o:o[0]+rng.random()*0.015)
            chosen[t]=item; raw+=item[1]
            for c in item[2]: used[c]+=1
        # subgradient: overused courier price up, unused down (target exactly once)
        step=2.8/math.sqrt(it+4)
        for c in prices:
            prices[c]+=step*(used[c]-1)
            if prices[c]>80: prices[c]=80
            elif prices[c]<-80: prices[c]=-80
        for t,item in chosen.items():
            best_cols.setdefault(t,{})[item[2]]=item
    # seed with baseline columns and final neutral/dual options
    for t,rows in base_sel.items():
        cids=tuple(r[2] for r in rows); best_cols.setdefault(t,{})[cids]=(row_group_cost(rows),row_group_cost(rows),cids,tuple(rows))
    for pr in (prices,{c:0.0 for c in prices}):
        opts=build_task_options(C,B,pr,top=22,keep=55)
        for t,os in opts.items():
            for item in os: best_cols.setdefault(t,{})[item[2]]=item
    return best_cols,base

def greedy_construct(best_cols,B,tries=2500,seed=11):
    rng=random.Random(seed); tasks=sorted(B)
    opts={t:sorted(best_cols.get(t,{}).values(),key=lambda x:(x[1],len(x[2])))[:90] for t in tasks}
    best=None; best_cost=1e99
    for tr in range(tries):
        used=set(); sel={}; cost=0.0
        order=tasks[:]
        if tr: rng.shuffle(order)
        else: order.sort(key=lambda t: len(opts[t]))
        ok=True
        for t in order:
            feas=[o for o in opts[t] if not (set(o[2])&used)]
            if not feas: ok=False; break
            if tr%5==0: pick=feas[0]
            else:
                pool=feas[:min(len(feas),8+(tr%11))]
                pick=min(pool,key=lambda o:o[1]+rng.random()*(0.6+0.03*(tr%17)))
            sel[t]=pick[3]; used.update(pick[2]); cost+=pick[1]
        if ok and cost<best_cost:
            best_cost=cost; best=sel
    return fmt(best) if best else []

def main():
    global ARG
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--rounds',type=int,default=130); ap.add_argument('--tries',type=int,default=1800)
    ARG=ap.parse_args()
    text,C,B=parse(ARG.input)
    base=s.solve(text); globals()['BASE_OUT']=base; basecost=s._solution_expected_cost(base,C,B)
    print('base',basecost, 'groups',len(base), 'k',collections.Counter(len(x[1]) for x in base), flush=True)
    cols,base=lagrangian(C,B,ARG.rounds)
    print('cols',sum(len(v) for v in cols.values()), 'per_task_minmax', min(len(v) for v in cols.values()), max(len(v) for v in cols.values()))
    out=greedy_construct(cols,B,ARG.tries)
    if out:
        cost=s._solution_expected_cost(out,C,B)
        print('greedy_best',cost,'delta',cost-basecost,'groups',len(out),'k',collections.Counter(len(x[1]) for x in out),'used',len({c for _,cs in out for c in cs}))
        for row in out: print(row)
    else: print('no feasible')
if __name__=='__main__': main()
