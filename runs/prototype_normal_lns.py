#!/usr/bin/env python3
from __future__ import annotations
import argparse, random, sys, time
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Set
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import solver  # type: ignore
Cand=Tuple[str,Tuple[str,...],str,float,float,int]
Result=List[Tuple[str,List[str]]]

def parse(text:str):
    lines=text.strip().splitlines(); start=1 if lines and lines[0].startswith('task_id_list') else 0
    c=[]; tasks=set()
    for rid,line in enumerate(lines[start:]):
        p=line.strip().split('\t')
        if len(p)<4: continue
        tk,co,sc,w=p[:4]; ts=tuple(x.strip() for x in tk.split(',') if x.strip())
        if not ts or not co: continue
        try: scf=float(sc); wf=float(w)
        except: continue
        c.append((tk.strip(),ts,co.strip(),scf,wf,rid)); tasks.update(ts)
    return c,sorted(tasks)

def cost(res:Result,cands:Sequence[Cand],tasks:Sequence[str]):
    return solver._solution_expected_cost(res,list(cands),set(tasks)) # type: ignore[attr-defined]

def cov(res:Result,cands:Sequence[Cand]):
    return solver._solution_covered_count(res,list(cands)) # type: ignore[attr-defined]

def selected(res:Result,cands:Sequence[Cand]):
    mp={(a[0],a[2]):a for a in cands}; out={}
    for tk,cs in res:
        rows=[mp.get((tk,c)) for c in cs]; rows=[r for r in rows if r is not None]
        if rows: out[tk]=rows
    return out

def group_cost(rows): return solver._group_expected_cost(tuple(rows),len(rows[0][1])) # type: ignore[attr-defined]

def adjacency(cands:Sequence[Cand]):
    adj={}
    for tk,ts,co,sc,w,rid in cands:
        for t in ts:
            s=adj.setdefault(t,set())
            s.update(x for x in ts if x!=t)
    return adj

def windows(res:Result,cands:Sequence[Cand],tasks:Sequence[str],maxw:int,seed:int):
    sel=selected(res,cands); adj=adjacency(cands); W=[]; seen=set()
    scored=[]
    for tk,rows in sel.items():
        ts=set(rows[0][1]); gc=group_cost(rows); scored.append((gc/max(1,len(ts)),gc,ts,tk))
    scored.sort(reverse=True)
    def add(s):
        if not s: return
        q=tuple(sorted(s))
        if len(q)>maxw: q=q[:maxw]
        if q and q not in seen: seen.add(q); W.append(set(q))
    for i in range(min(12,len(scored))):
        s=set()
        for _,_,ts,_ in scored[i:i+3]: s.update(ts)
        add(s)
    for _,_,ts,_ in scored[:12]:
        s=set(ts)
        for t in list(ts):
            for u in sorted(adj.get(t,())):
                s.add(u)
                if len(s)>=maxw: break
            if len(s)>=maxw: break
        add(s)
    # bundle attractors: good candidate bundles not fully matching current window
    bundle_rank=[]
    for r in cands:
        if len(r[1])>=2:
            g=solver._group_expected_cost((r,),len(r[1])) # type: ignore[attr-defined]
            saving=100*len(r[1])-g
            if saving>0: bundle_rank.append((saving/max(1,g),saving,set(r[1])))
    bundle_rank.sort(reverse=True)
    for _,_,ts in bundle_rank[:20]:
        s=set(ts)
        for t in list(ts):
            for u in sorted(adj.get(t,())):
                s.add(u)
                if len(s)>=maxw: break
            if len(s)>=maxw: break
        add(s)
    rnd=random.Random(seed)
    base=[set(ts) for _,_,ts,_ in scored[:16]] or [{t} for t in tasks]
    for _ in range(24):
        s=set(rnd.choice(base))
        while len(s)<maxw and rnd.random()<0.8:
            frontier=sorted({u for t in s for u in adj.get(t,set()) if u not in s})
            if not frontier: break
            s.add(rnd.choice(frontier))
        add(s)
    return W

def repair_window(cur:Result,cands:Sequence[Cand],tasks:Sequence[str],win:Set[str],deadline:float,top:int,maxk:int,opt:int):
    mp={(a[0],a[2]):a for a in cands}; sel=solver._result_to_selected(cur,mp) # type: ignore[attr-defined]
    return solver._repair_task_window(sel,list(cands),set(tasks),set(win),deadline,top_riders_per_task_key=top,max_k=maxk,option_limit=opt) # type: ignore[attr-defined]

def run(text:str,seconds:float,maxw:int,rounds:int):
    cands,tasks=parse(text); start=time.monotonic()
    cur=solver.solve(text); deadline=time.monotonic()+seconds; best=cur; bc=cost(cur,cands,tasks); basec=bc; basecov=cov(cur,cands)
    tried=0; improved=0
    for r in range(rounds):
        if time.monotonic()>deadline-.2: break
        changed=False
        for win in windows(best,cands,tasks,maxw,20260521+r*97+len(cands)):
            if time.monotonic()>deadline-.12: break
            tried+=1
            cand=repair_window(best,cands,tasks,win,min(deadline,time.monotonic()+0.18),top=14,maxk=5,opt=120)
            if not cand: continue
            if time.monotonic()<deadline-.08:
                cand=solver._reassign_mixed_solution(cand,list(cands),set(tasks),min(deadline,time.monotonic()+.06)) # type: ignore[attr-defined]
            cc=cost(cand,cands,tasks)
            if cov(cand,cands)>=basecov and cc<bc-1e-9:
                best=cand; bc=cc; improved+=1; changed=True
                print('improve',improved,'round',r,'win',sorted(win),'cost',bc,'delta',bc-basec)
                break
        if not changed: break
    return cands,tasks,cur,best,basec,bc,tried,improved,time.monotonic()-start

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--seconds',type=float,default=6); ap.add_argument('--maxw',type=int,default=14); ap.add_argument('--rounds',type=int,default=4)
    a=ap.parse_args(); text=Path(a.input).read_text(); c,t,cur,best,base,bc,tried,imp,elapsed=run(text,a.seconds,a.maxw,a.rounds)
    print(f'base={base:.6f} best={bc:.6f} delta={bc-base:+.6f} cov={cov(best,c)}/{len(t)} groups={len(best)} tried={tried} imp={imp} elapsed={elapsed:.3f}s')
    if bc<base-1e-9: print(best)
if __name__=='__main__': main()
