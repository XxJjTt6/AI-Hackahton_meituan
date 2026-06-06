#!/usr/bin/env python3
import importlib.util,pathlib,itertools,json,argparse,time
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
        try: cost=float(cost); prob=float(prob)
        except: continue
        C.append((tk,tasks,cid,cost,prob,idx)); B.update(tasks)
    return C,B

def main():
    # Use official scarce cached solution shape; evaluate only on synthetic/public scarce input if passed.
    ap=argparse.ArgumentParser(); ap.add_argument('input'); args=ap.parse_args()
    text=open(args.input).read(); C,B=parse(text)
    base=s.solve(text); basecost=s._solution_expected_cost(base,C,B)
    row={(r[0],r[2]):r for r in C}; sel=s._result_to_selected(base,row)
    print('base',basecost,'groups',len(base),'cov',s._solution_covered_count(base,C))
    tasks=list(sel); best=(basecost,None)
    # Try same coverage two-group courier swaps only; no uncovered/T0033 forcing.
    for a,b in itertools.combinations(tasks,2):
        ra=sel[a]; rb=sel[b]
        if len(ra)!=1 or len(rb)!=1: continue
        ca=ra[0][2]; cb=rb[0][2]
        na=row.get((a,cb)); nb=row.get((b,ca))
        if not na or not nb: continue
        old=s._group_expected_cost(ra,len(ra[0][1]))+s._group_expected_cost(rb,len(rb[0][1]))
        new=s._group_expected_cost([na],len(na[1]))+s._group_expected_cost([nb],len(nb[1]))
        if new<old-1e-9:
            cand=[]
            for k,cs in base:
                if k==a: cand.append((k,[cb]))
                elif k==b: cand.append((k,[ca]))
                else: cand.append((k,cs))
            total=s._solution_expected_cost(cand,C,B)
            if total<best[0]: best=(total,(a,b,ca,cb,new-old)); print('IMPROVE',total,total-basecost,best[1])
    # 3-cycle courier swaps, same coverage only
    for a,b,c in itertools.combinations(tasks,3):
        rs=[sel[a],sel[b],sel[c]]
        if any(len(x)!=1 for x in rs): continue
        cs=[rs[0][0][2],rs[1][0][2],rs[2][0][2]]
        old=sum(s._group_expected_cost(sel[t],len(sel[t][0][1])) for t in (a,b,c))
        for perm in ((cs[1],cs[2],cs[0]),(cs[2],cs[0],cs[1])):
            rows=[]; ok=True
            for t,cour in zip((a,b,c),perm):
                r=row.get((t,cour))
                if not r: ok=False; break
                rows.append(r)
            if not ok: continue
            new=sum(s._group_expected_cost([r],len(r[1])) for r in rows)
            if new<old-1e-9:
                cand=[]
                mp={a:[perm[0]],b:[perm[1]],c:[perm[2]]}
                for k,cs0 in base: cand.append((k,mp.get(k,cs0)))
                total=s._solution_expected_cost(cand,C,B)
                if total<best[0]: best=(total,(a,b,c,perm,new-old)); print('IMPROVE3',total,total-basecost,best[1])
    print('best',best[0],best[0]-basecost,best[1])
if __name__=='__main__': main()
