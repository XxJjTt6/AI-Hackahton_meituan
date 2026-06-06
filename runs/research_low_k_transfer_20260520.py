#!/usr/bin/env python3
import importlib.util,pathlib,itertools,argparse
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
    ap=argparse.ArgumentParser(); ap.add_argument('input'); args=ap.parse_args()
    text=open(args.input).read(); C,B=parse(text)
    base=s.solve(text); basecost=s._solution_expected_cost(base,C,B)
    row={(r[0],r[2]):r for r in C}; sel=s._result_to_selected(base,row)
    print('base',basecost,'sizes',sorted((k,len(v)) for k,v in sel.items())[:5], 'n',len(sel))
    best=(basecost,None)
    tasks=list(sel)
    # one transfer: remove a courier from source task, add to target task, no reuse issue by construction.
    for src,dst in itertools.permutations(tasks,2):
        for rr in sel[src]:
            c=rr[2]
            add=row.get((dst,c))
            if not add: continue
            old=s._group_expected_cost(sel[src],1)+s._group_expected_cost(sel[dst],1)
            new_src=[x for x in sel[src] if x[2]!=c]
            new_dst=sel[dst]+[add]
            if not new_src: continue
            new=s._group_expected_cost(new_src,1)+s._group_expected_cost(new_dst,1)
            if new<old-1e-9:
                cand=[]
                for k,cs in base:
                    if k==src: cand.append((k,[x[2] for x in new_src]))
                    elif k==dst: cand.append((k,[x[2] for x in new_dst]))
                    else: cand.append((k,cs))
                total=s._solution_expected_cost(cand,C,B)
                if total<best[0]: best=(total,(src,dst,c,new-old)); print('IMPROVE1',total,total-basecost,best[1])
    # two independent transfers greedy from current best is not necessary if no single transfer improves; test pair swap+transfer combined by small windows could be later.
    print('best',best[0],best[0]-basecost,best[1])
if __name__=='__main__': main()
