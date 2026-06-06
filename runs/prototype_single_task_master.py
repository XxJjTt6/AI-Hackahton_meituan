#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys, time, itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import solver  # type: ignore

def parse(text):
    lines=text.strip().splitlines(); st=1 if lines and lines[0].startswith('task_id_list') else 0
    c=[]; tasks=set()
    for rid,line in enumerate(lines[st:]):
        p=line.split('\t')
        if len(p)<4: continue
        tk,co,sc,w=p[:4]; ts=tuple(x for x in tk.split(',') if x)
        try: sc=float(sc); w=float(w)
        except: continue
        c.append((tk,ts,co,sc,w,rid)); tasks.update(ts)
    return c,sorted(tasks)

def gc(rows,tc=1): return solver._group_expected_cost(tuple(rows),tc) # type: ignore[attr-defined]
def scost(res,cands,tasks): return solver._solution_expected_cost(res,cands,set(tasks)) # type: ignore[attr-defined]
def cov(res,cands): return solver._solution_covered_count(res,cands) # type: ignore[attr-defined]

def incumbent_counts(res): return {tk:len(cs) for tk,cs in res}

def build_columns(cands,tasks,maxk,top,per_task,inc,inc_res):
    by={t:[] for t in tasks}
    for r in cands:
        if len(r[1])==1: by.setdefault(r[1][0],[]).append(r)
    cols=[]
    inc_map={tk:tuple(cs) for tk,cs in inc_res}
    by_key={(r[1][0],r[2]):r for r in cands if len(r[1])==1}
    for t in tasks:
        rows=sorted(by.get(t,[]), key=lambda r:(gc((r,),1), -r[4], r[5]))[:top]
        opts=[]; inc_k=inc.get(t)
        for k in range(1,min(maxk,len(rows))+1):
            for comb in itertools.combinations(rows,k):
                cost=gc(comb,1); cm=tuple(sorted(r[2] for r in comb))
                # keep all incumbent cardinalities in the option set; otherwise top by cost
                bonus=0 if k==inc_k else 1
                opts.append((cost,bonus,cm,comb))
        inc_cs=inc_map.get(t)
        if inc_cs:
            inc_rows=tuple(by_key.get((t,c)) for c in inc_cs)
            if all(inc_rows):
                inc_rows=tuple(r for r in inc_rows if r)
                opts.append((gc(inc_rows,1)-10000,-1,tuple(sorted(r[2] for r in inc_rows)),inc_rows))
        opts.sort(key=lambda x:(x[1],x[0],len(x[2])))
        for cost,bonus,cm,comb in opts[:per_task]: cols.append((t,gc(comb,1),cm,comb))
    return cols

def beam_solve(cols,tasks,width,inc_res=None):
    by={t:[] for t in tasks}
    for col in cols: by[col[0]].append(col)
    for t in tasks: by[t].sort(key=lambda x:(x[1],len(x[2])))
    inc_by={tk:tuple(cs) for tk,cs in (inc_res or [])}
    inc_prefix=(0.0,frozenset(),[])
    states=[(0.0,frozenset(),[])]
    for t in tasks:
        ns=[]
        # force incumbent prefix to survive every layer
        if t in inc_by:
            inc_col=None
            for col in by.get(t,[]):
                if tuple(sorted(col[2]))==tuple(sorted(inc_by[t])):
                    inc_col=col; break
            if inc_col is not None and not (inc_prefix[1] & set(inc_col[2])):
                inc_prefix=(inc_prefix[0]+inc_col[1], inc_prefix[1]|set(inc_col[2]), inc_prefix[2]+[(t,list(inc_by[t]))])
                ns.append(inc_prefix)
        for cost,used,path in states:
            # allow uncovered, but usually dominated
            ns.append((cost+100,used,path))
            for _,cc,cs,comb in by.get(t,[])[:80]:
                s=set(cs)
                if used & s: continue
                ns.append((cost+cc, used|s, path+[(t,[r[2] for r in sorted(comb,key=lambda r:(r[3],-r[4],r[5]))])]))
        ns.sort(key=lambda x:(x[0], -len(x[2]), len(x[1])))
        # diversity by used couriers fingerprint
        out=[]; seen=set()
        for st in ns:
            key=st[1]
            if key in seen: continue
            seen.add(key); out.append(st)
            if len(out)>=width: break
        states=out
    return min(states,key=lambda x:x[0])[2]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--maxk',type=int,default=3); ap.add_argument('--top',type=int,default=14); ap.add_argument('--per-task',type=int,default=90); ap.add_argument('--width',type=int,default=8000)
    a=ap.parse_args(); text=Path(a.input).read_text(); c,t=parse(text); start=time.monotonic(); inc=solver.solve(text); ic=scost(inc,c,t); cols=build_columns(c,t,a.maxk,a.top,a.per_task,incumbent_counts(inc),inc); res=beam_solve(cols,t,a.width,inc); rc=scost(res,c,t)
    print(f'tasks={len(t)} cols={len(cols)} inc={ic:.6f} master={rc:.6f} delta={rc-ic:+.6f} cov={cov(res,c)}/{len(t)} groups={len(res)} elapsed={time.monotonic()-start:.3f}s')
    if rc<ic-1e-9: print(res)
if __name__=='__main__': main()
