#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys, time, itertools
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

def gc(rows,tc=None):
    if not rows: return 100.0*(tc or 1)
    return solver._group_expected_cost(tuple(rows), len(rows[0][1]) if tc is None else tc) # type: ignore[attr-defined]
def scost(res,cands,tasks): return solver._solution_expected_cost(res,cands,set(tasks)) # type: ignore[attr-defined]
def cov(res,cands): return solver._solution_covered_count(res,cands) # type: ignore[attr-defined]
def fmt(S): return [(k,[r[2] for r in sorted(v,key=lambda r:(r[3],-r[4],r[5]))]) for k,v in sorted(S.items()) if v]
def selected(res,cands):
    mp={(r[0],r[2]):r for r in cands}; S={}
    for tk,cs in res:
        rows=[mp.get((tk,c)) for c in cs]; rows=[r for r in rows if r]
        if rows: S[tk]=rows
    return S

def improve_once(S,cands,tasks,deadline,top_pairs=180,top_bundles=6):
    rowmap={(r[0],r[2]):r for r in cands}
    bundles={}
    for r in cands:
        if len(r[1])==2:
            bundles.setdefault(tuple(sorted(r[1])),[]).append(r)
    for k in bundles:
        bundles[k].sort(key=lambda r: gc([r],2))
    singles=[k for k,v in S.items() if v and len(v[0][1])==1]
    group_cost={k:gc(v) for k,v in S.items()}
    # Prefer expensive pairs and pairs that have bundle rows.
    pairs=[]
    for a,b in itertools.combinations(singles,2):
        key=tuple(sorted((S[a][0][1][0], S[b][0][1][0])))
        if key not in bundles: continue
        pairs.append((group_cost[a]+group_cost[b],a,b,key))
    pairs.sort(reverse=True)
    base=scost(fmt(S),cands,tasks)
    best_delta=0.0; bestS=None; best_desc=None
    for _,a,b,key in pairs[:top_pairs]:
        if time.monotonic()>deadline-.05: break
        old_rows=S[a]+S[b]
        old_couriers={r[2] for r in old_rows}
        old_cost=group_cost[a]+group_cost[b]
        used_else={r[2] for k,rows in S.items() if k not in (a,b) for r in rows}
        for br in bundles[key][:top_bundles]:
            if br[2] in used_else: continue
            freed=list(old_couriers-{br[2]})
            T={k:list(v) for k,v in S.items() if k not in (a,b)}
            T[br[0]]=[br]
            # Greedily add freed couriers to target groups if marginal improves.
            improved=True
            while improved and freed and time.monotonic()<deadline-.05:
                improved=False; best_add=None; best_gain=0.0
                used={r[2] for rows in T.values() for r in rows}
                for courier in list(freed):
                    if courier in used: continue
                    for tk,rows in T.items():
                        if any(r[2]==courier for r in rows): continue
                        add=rowmap.get((tk,courier))
                        if not add: continue
                        before=gc(rows); after=gc(rows+[add],len(rows[0][1]))
                        gain=before-after
                        if gain>best_gain+1e-12:
                            best_gain=gain; best_add=(courier,tk,add)
                if best_add and best_gain>1e-9:
                    courier,tk,add=best_add; T[tk].append(add); freed.remove(courier); improved=True
            res=fmt(T); cc=scost(res,cands,tasks); delta=cc-base
            if cov(res,cands)==len(tasks) and delta<best_delta-1e-9:
                best_delta=delta; bestS=T; best_desc=(a,b,br[0],br[2],delta,cc)
    return bestS,best_delta,best_desc

def improve(res,cands,tasks,seconds):
    deadline=time.monotonic()+seconds; S=selected(res,cands); moves=0
    while time.monotonic()<deadline-.1:
        T,delta,desc=improve_once(S,cands,tasks,deadline)
        if T is None: break
        S=T; moves+=1; print('exchange',moves,desc)
    return fmt(S),moves

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--seconds',type=float,default=8)
    a=ap.parse_args(); text=Path(a.input).read_text(); c,t=parse(text); start=time.monotonic(); inc=solver.solve(text); ic=scost(inc,c,t); res,m=improve(inc,c,t,a.seconds); rc=scost(res,c,t)
    print(f'inc={ic:.6f} bundle_redist={rc:.6f} delta={rc-ic:+.6f} cov={cov(res,c)}/{len(t)} groups={len(res)} moves={m} elapsed={time.monotonic()-start:.3f}s')
    if rc<ic-1e-9: print(res)
if __name__=='__main__': main()
