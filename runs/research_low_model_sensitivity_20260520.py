#!/usr/bin/env python3
import importlib.util,pathlib,argparse,itertools,time,math
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
        if not tasks or not cid: continue
        try: cost=float(cost); prob=float(prob)
        except: continue
        C.append((tk,tasks,cid,cost,prob,idx)); B.update(tasks)
    return C,B

def transform(C,prob_alpha=1.0,cost_alpha=1.0,penalty=100.0):
    # emulate judge-model misspecification: p^alpha and cost scaling. penalty handled by monkeypatch extra impossible via p/cost transform only approximate.
    out=[]
    for tk,tasks,cid,cost,p,idx in C:
        pp=max(0.0,min(1.0,p**prob_alpha))
        out.append((tk,tasks,cid,cost*cost_alpha,pp,idx))
    return out

def result_sig(r): return '\n'.join(f'{k}:{",".join(v)}' for k,v in r)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); args=ap.parse_args()
    text=open(args.input).read(); C,B=parse(text)
    base=s.solve(text); basecost=s._solution_expected_cost(base,C,B); basesig=result_sig(base)
    print('base',basecost)
    candidates=[]
    for pa in [0.7,0.8,0.9,1.0,1.1,1.2,1.35,1.5]:
        for ca in [0.7,0.85,1.0,1.15,1.3]:
            CC=transform(C,pa,ca)
            # run main building blocks under transformed model, evaluate back on original.
            E=[]; H=[x for x in CC if len(x[1])==1]
            deadline=time.monotonic()+1.8
            if H: E.append(s._solve_single_task_multidispatch(H,B))
            if time.monotonic()<deadline-.5: E.append(s._solve_pair_potential_matching(CC,B,deadline,lookahead=6,flexible_initial=True))
            if time.monotonic()<deadline-.5: E.append(s._search_column_window(H,B,min(deadline,time.monotonic()+.8),top_riders_per_task_key=14,max_k=4,option_limit=80))
            for r in E:
                if not r: continue
                cost=s._solution_expected_cost(r,C,B); sig=result_sig(r)
                candidates.append((cost,pa,ca,len(r),sig==basesig,r))
                if cost<basecost-1e-9: print('IMPROVE',cost,cost-basecost,'pa',pa,'ca',ca,'n',len(r),'same',sig==basesig)
    candidates.sort(key=lambda x:x[0])
    seen=set(); print('top')
    for cost,pa,ca,n,same,r in candidates:
        sig=result_sig(r)
        if sig in seen: continue
        seen.add(sig)
        print(cost,cost-basecost,'pa',pa,'ca',ca,'n',n,'same',same)
        if len(seen)>=12: break
if __name__=='__main__': main()
