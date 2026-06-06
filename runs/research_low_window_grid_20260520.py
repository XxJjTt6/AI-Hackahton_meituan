#!/usr/bin/env python3
import argparse, importlib.util, time, itertools, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('solver_mod', ROOT/'solver.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)

def parse(text):
    lines=text.strip().splitlines(); off=1 if lines and lines[0].startswith('task') else 0
    C=[]; B=set()
    for idx,line in enumerate(lines[off:]):
        parts=line.strip().split('\t')
        if len(parts)<4: continue
        tk, cid, cost, p = parts[:4]
        tasks=tuple(x.strip() for x in tk.split(',') if x.strip())
        if not tasks or not cid: continue
        try: cost=float(cost); p=float(p)
        except ValueError: continue
        C.append((tk, tasks, cid, cost, p, idx))
        B.update(tasks)
    return C,B

def sig(result):
    return tuple((k, tuple(v)) for k,v in result)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input')
    ap.add_argument('--seconds',type=float,default=45)
    args=ap.parse_args()
    text=open(args.input).read()
    C,B=parse(text)
    base=s.solve(text)
    base_cost=s._solution_expected_cost(base,C,B)
    print('base', base_cost, 'groups', len(base), 'sig', hash(sig(base)))
    variants=[]
    # official low branch internally biases p by alpha .3 first; test both original and biased pools.
    pools=[('orig',text,C), ('bias03', s._bias_low_input_text(text,.3), None)]
    deadline_all=time.monotonic()+args.seconds
    for pname,ptext,pool in pools:
        if pool is None: pool,_=parse(ptext)
        singles=[x for x in pool if len(x[1])==1]
        for source, cand in [('all',pool),('singles',singles)]:
            if not cand: continue
            for top,maxk,opt,span in itertools.product([8,10,12,14,16,20],[2,3,4,5,6],[28,55,90,140,220],[0.45,0.8,1.3,2.0]):
                if time.monotonic()>deadline_all: break
                if source=='singles' and maxk>5: continue
                d=time.monotonic()+span
                s._GROUP_COST_CACHE={}
                r=s._search_column_window(cand,B,d,top_riders_per_task_key=top,max_k=maxk,option_limit=opt)
                if not r: continue
                # Evaluate selected output on original candidates.
                cost=s._solution_expected_cost(r,C,B)
                variants.append((cost,pname,source,top,maxk,opt,span,len(r),sig(r)))
                if cost < base_cost-1e-6:
                    print('IMPROVE', cost, 'delta', cost-base_cost, pname, source, top,maxk,opt,span,'groups',len(r))
        if time.monotonic()>deadline_all: break
    variants.sort(key=lambda x:x[0])
    print('top variants')
    seen=set()
    for row in variants[:20]:
        key=row[8]
        if key in seen: continue
        seen.add(key)
        print(row[:8], 'delta', row[0]-base_cost)
        if len(seen)>=10: break

if __name__=='__main__': main()
