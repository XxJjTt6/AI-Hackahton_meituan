#!/usr/bin/env python3
from __future__ import annotations
import argparse, random, sys, time, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
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
def gc(rows,tc=1): return solver._group_expected_cost(tuple(rows),tc) # type: ignore[attr-defined]
def scost(res,cands,tasks): return solver._solution_expected_cost(res,cands,set(tasks)) # type: ignore[attr-defined]
def selected(res,cands):
    mp={(r[0],r[2]):r for r in cands}; S={}
    for tk,cs in res:
        rows=[mp.get((tk,c)) for c in cs]; rows=[r for r in rows if r]
        if rows and len(rows[0][1])==1: S[tk]=rows
    return S
def fmt(S): return [(k,[r[2] for r in sorted(v,key=lambda r:(r[3],-r[4],r[5]))]) for k,v in sorted(S.items())]

def improve(res,cands,tasks,seconds,seed=1):
    rng=random.Random(seed); rowmap={(r[0],r[2]):r for r in cands if len(r[1])==1}; S=selected(res,cands)
    if len(S)!=len(tasks): return res,0
    keys=list(S); cur=sum(gc(v,1) for v in S.values()); best=cur; bestS={k:list(v) for k,v in S.items()}; moves=0; deadline=time.monotonic()+seconds; it=0
    while time.monotonic()<deadline:
        it+=1; temp=max(0.01, 2.0*(1-(time.monotonic()-(deadline-seconds))/seconds))
        if rng.random()<0.75:
            a,b=rng.sample(keys,2); ia=rng.randrange(len(S[a])); ib=rng.randrange(len(S[b])); ca=S[a][ia][2]; cb=S[b][ib][2]
            ra=rowmap.get((a,cb)); rb=rowmap.get((b,ca))
            if not ra or not rb: continue
            old=gc(S[a],1)+gc(S[b],1)
            na=list(S[a]); nb=list(S[b]); na[ia]=ra; nb[ib]=rb
            new=gc(na,1)+gc(nb,1); delta=new-old
            if delta<0 or rng.random()<math.exp(-delta/temp):
                S[a]=na; S[b]=nb; cur+=delta; moves+=1
        else:
            a,b,c=rng.sample(keys,3); ia=rng.randrange(len(S[a])); ib=rng.randrange(len(S[b])); ic=rng.randrange(len(S[c]))
            ca,cb,cc=S[a][ia][2],S[b][ib][2],S[c][ic][2]
            # rotate ca->b, cb->c, cc->a
            ra=rowmap.get((a,cc)); rb=rowmap.get((b,ca)); rc=rowmap.get((c,cb))
            if not ra or not rb or not rc: continue
            old=gc(S[a],1)+gc(S[b],1)+gc(S[c],1)
            na=list(S[a]); nb=list(S[b]); nc=list(S[c]); na[ia]=ra; nb[ib]=rb; nc[ic]=rc
            new=gc(na,1)+gc(nb,1)+gc(nc,1); delta=new-old
            if delta<0 or rng.random()<math.exp(-delta/temp):
                S[a]=na; S[b]=nb; S[c]=nc; cur+=delta; moves+=1
        if cur<best-1e-9:
            best=cur; bestS={k:list(v) for k,v in S.items()}; print('best',best,'delta',best-scost(res,cands,tasks),'it',it,'moves',moves)
    return fmt(bestS),moves

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--seconds',type=float,default=10); ap.add_argument('--seed',type=int,default=1)
    a=ap.parse_args(); text=Path(a.input).read_text(); c,t=parse(text); start=time.monotonic(); inc=solver.solve(text); ic=scost(inc,c,t); res,m=improve(inc,c,t,a.seconds,a.seed); rc=scost(res,c,t)
    print(f'inc={ic:.6f} sa={rc:.6f} delta={rc-ic:+.6f} moves={m} elapsed={time.monotonic()-start:.3f}s')
    if rc<ic-1e-9: print(res)
if __name__=='__main__': main()
