#!/usr/bin/env python3
import importlib.util, pathlib, itertools, argparse, time
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

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--limit',type=int,default=3); args=ap.parse_args()
    text=open(args.input).read(); C,B=parse(text)
    out=s.solve(text); base=s._solution_expected_cost(out,C,B)
    row={(r[0],r[2]):r for r in C}
    sel=s._result_to_selected(out,row)
    print('base',base,'groups',len(sel),'sizes',sorted(set(len(v) for v in sel.values())))
    best=(base,None,None)
    tasks=list(sel)
    for m in range(2,args.limit+1):
        checked=0
        for ts in itertools.combinations(tasks,m):
            checked+=1
            riders=[r[2] for t in ts for r in sel[t]]
            if len(riders)!=len(set(riders)): continue
            old=sum(s._group_expected_cost(sel[t],len(sel[t][0][1])) for t in ts)
            # low official shape is 2 per task; enumerate pair partitions for m<=3.
            if m==2:
                assigns=[]
                for pair in itertools.combinations(riders,2):
                    rem=tuple(r for r in riders if r not in pair)
                    assigns.append((pair,rem))
            else:
                assigns=[]
                riders_t=tuple(riders)
                for p1 in itertools.combinations(riders_t,2):
                    rem1=tuple(r for r in riders_t if r not in p1)
                    for p2 in itertools.combinations(rem1,2):
                        p3=tuple(r for r in rem1 if r not in p2)
                        assigns.append((p1,p2,p3))
            for assign in assigns:
                for perm in itertools.permutations(assign):
                    rows=[]; ok=True; new=0
                    for t,pair in zip(ts,perm):
                        rr=[]
                        for c in pair:
                            r=row.get((t,c))
                            if not r: ok=False; break
                            rr.append(r)
                        if not ok: break
                        new += s._group_expected_cost(rr,len(rr[0][1])); rows.append((t,rr))
                    if ok and new < old-1e-9:
                        total=base-old+new
                        if total<best[0]: best=(total,ts,perm); print('IMPROVE m',m,'total',total,'delta',total-base,'local',new-old,'tasks',ts,'assign',perm)
        print('done m',m,'checked',checked,'best_delta',best[0]-base)
    print('best',best[0],best[0]-base,best[1],best[2])
if __name__=='__main__': main()
