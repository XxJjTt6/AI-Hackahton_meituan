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
        except: pass
    return c,sorted(tasks)

def gc(rows,tc=1): return solver._group_expected_cost(tuple(rows),tc) # type: ignore[attr-defined]
def scost(res,cands,tasks): return solver._solution_expected_cost(res,cands,set(tasks)) # type: ignore[attr-defined]
def fmt(sel): return [(k,[r[2] for r in sorted(v,key=lambda r:(r[3],-r[4],r[5]))]) for k,v in sorted(sel.items()) if v]
def sel(res,cands):
    mp={(r[0],r[2]):r for r in cands}; out={}
    for tk,cs in res:
        rs=[mp.get((tk,c)) for c in cs]; rs=[r for r in rs if r]
        if rs: out[tk]=rs
    return out

def improve(res,cands,tasks,seconds):
    deadline=time.monotonic()+seconds; S=sel(res,cands); by={(r[0],r[2]):r for r in cands}; best=scost(fmt(S),cands,tasks); moves=0
    while time.monotonic()<deadline-.05:
        best_move=None; best_delta=0.0
        # one-rider relocation: remove courier from source group, add to target same-task key if row exists
        for sk,srows in list(S.items()):
            if len(srows)<=1: continue
            old_s=gc(srows,len(srows[0][1]))
            for r in list(srows):
                new_srows=[x for x in srows if x!=r]
                ds=gc(new_srows,len(srows[0][1]))-old_s
                courier=r[2]
                for tk,trows in S.items():
                    if tk==sk or any(x[2]==courier for x in trows): continue
                    add=by.get((tk,courier))
                    if not add: continue
                    old_t=gc(trows,len(trows[0][1])); new_t=gc(trows+[add],len(trows[0][1]))
                    delta=ds+(new_t-old_t)
                    if delta<best_delta-1e-12:
                        best_delta=delta; best_move=(sk,tk,r,add,delta)
        if not best_move: break
        sk,tk,r,add,delta=best_move
        S[sk]=[x for x in S[sk] if x!=r]; S[tk].append(add); moves+=1; best+=delta
        print('move',moves,r[2],sk,'->',tk,'delta',delta,'cost',best)
    return fmt(S),moves

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--seconds',type=float,default=3)
    a=ap.parse_args(); text=Path(a.input).read_text(); c,t=parse(text); start=time.monotonic(); inc=solver.solve(text); ic=scost(inc,c,t); res,moves=improve(inc,c,t,a.seconds); rc=scost(res,c,t)
    print(f'inc={ic:.6f} redist={rc:.6f} delta={rc-ic:+.6f} moves={moves} elapsed={time.monotonic()-start:.3f}s')
    if rc<ic-1e-9: print(res)
if __name__=='__main__': main()
