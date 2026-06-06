#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys, time
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
        try: c.append((tk,ts,co,float(sc),float(w),rid)); tasks.update(ts)
        except Exception: pass
    return c,sorted(tasks)

def gc(rows,tc=None):
    if not rows: return 100.0*(tc or 1)
    return solver._group_expected_cost(tuple(rows),len(rows[0][1]) if tc is None else tc) # type: ignore[attr-defined]
def scost(res,cands,tasks): return solver._solution_expected_cost(res,cands,set(tasks)) # type: ignore[attr-defined]
def cov(res,cands): return solver._solution_covered_count(res,cands) # type: ignore[attr-defined]
def fmt(S): return [(k,[r[2] for r in sorted(v,key=lambda r:(r[3],-r[4],r[5]))]) for k,v in sorted(S.items()) if v]
def selected(res,cands):
    mp={(r[0],r[2]):r for r in cands}; S={}
    for tk,cs in res:
        rows=[mp.get((tk,c)) for c in cs]; rows=[r for r in rows if r]
        if rows: S[tk]=rows
    return S

def clone(S): return {k:list(v) for k,v in S.items()}

def apply_replace(S, task, incoming, outgoing):
    rows=S[task]
    S[task]=[r for r in rows if r[2]!=outgoing[2]]+[incoming]

def apply_add(S, task, incoming): S[task]=S[task]+[incoming]
def apply_remove(S, task, outgoing): S[task]=[r for r in S[task] if r[2]!=outgoing[2]]

def find_best_path(S,cands,rowmap,deadline,max_depth=4,branch=16):
    base={k:gc(v) for k,v in S.items()}; tasks=list(S)
    best_delta=0.0; best_ops=None
    # candidate starts: remove low marginal riders from groups with at least 2 riders
    starts=[]
    for sk,rows in S.items():
        if len(rows)<=1: continue
        old=base[sk]
        for r in rows:
            rem=[x for x in rows if x[2]!=r[2]]
            delta=gc(rem)-old
            starts.append((delta,sk,r))
    starts.sort(key=lambda x:x[0])
    def dfs(curS, free_row, depth, delta, ops, visited_tasks):
        nonlocal best_delta,best_ops
        if time.monotonic()>deadline: return
        if depth>max_depth: return
        free_c=free_row[2]
        # rank possible target rows for this free courier
        opts=[]
        for tk,rows in curS.items():
            if tk in visited_tasks: continue
            if any(r[2]==free_c for r in rows): continue
            inc=rowmap.get((tk,free_c))
            if inc is None: continue
            old=gc(rows)
            # terminate by adding free courier to this task
            add_delta=gc(rows+[inc])-old
            opts.append((delta+add_delta, 'add', tk, inc, None, add_delta))
            # continue by replacing one rider in target with free courier
            if len(rows)>=1:
                for out in rows:
                    newrows=[r for r in rows if r[2]!=out[2]]+[inc]
                    rep_delta=gc(newrows)-old
                    opts.append((delta+rep_delta, 'rep', tk, inc, out, rep_delta))
        opts.sort(key=lambda x:x[0])
        for total,typ,tk,inc,out,step_delta in opts[:branch]:
            if typ=='add':
                if total<best_delta-1e-12:
                    best_delta=total; best_ops=ops+[('add',tk,inc,None,total)]
            else:
                newS=clone(curS); apply_replace(newS,tk,inc,out)
                dfs(newS,out,depth+1,total,ops+[('rep',tk,inc,out,total)],visited_tasks|{tk})
    for start_delta,sk,free in starts[:branch*2]:
        cur=clone(S); apply_remove(cur,sk,free)
        dfs(cur,free,1,start_delta,[('remove',sk,free,None,start_delta)],{sk})
    return best_delta,best_ops

def improve(res,cands,tasks,seconds,depth,branch):
    deadline=time.monotonic()+seconds; rowmap={(r[0],r[2]):r for r in cands}; S=selected(res,cands); basecov=cov(res,cands); base=scost(res,cands,tasks); moves=0
    while time.monotonic()<deadline-.05:
        delta,ops=find_best_path(S,cands,rowmap,deadline-.02,depth,branch)
        if not ops or delta>=-1e-9: break
        # apply path
        for typ,tk,inc,out,_td in ops:
            if typ=='remove': apply_remove(S,tk,inc)
            elif typ=='rep': apply_replace(S,tk,inc,out)
            elif typ=='add': apply_add(S,tk,inc)
        newres=fmt(S); newcost=scost(newres,cands,tasks)
        if cov(newres,cands)<basecov or newcost>base+delta+1e-6:
            break
        base=newcost; moves+=1
        print('path',moves,'delta',delta,'cost',base,'ops',[(o[0],o[1],o[2][2],o[3][2] if o[3] else None) for o in ops])
    return fmt(S),moves

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--seconds',type=float,default=5); ap.add_argument('--depth',type=int,default=4); ap.add_argument('--branch',type=int,default=14)
    a=ap.parse_args(); text=Path(a.input).read_text(); c,t=parse(text); start=time.monotonic(); inc=solver.solve(text); ic=scost(inc,c,t); res,moves=improve(inc,c,t,a.seconds,a.depth,a.branch); rc=scost(res,c,t)
    print(f'inc={ic:.6f} aug={rc:.6f} delta={rc-ic:+.6f} cov={cov(res,c)}/{len(t)} groups={len(res)} moves={moves} elapsed={time.monotonic()-start:.3f}s')
    if rc<ic-1e-9: print(res)
if __name__=='__main__': main()
