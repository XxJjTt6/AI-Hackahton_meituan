#!/usr/bin/env python3
from __future__ import annotations
import glob,json,math,time
from collections import defaultdict,Counter
from pathlib import Path
EXCLUDE={'scarce_couriers_seed401.txt','low_willingness_seed501.txt'}
PEN=100.0

def tasks_of(k): return tuple(x for x in str(k).split(',') if x)
def couriers_of(x): return tuple(x or ()) if isinstance(x,list) else tuple(str(x).split(','))

def collect():
    rows=defaultdict(dict); cases=defaultdict(list)
    for p in glob.glob('runs/official_*.json'):
        try: d=json.load(open(p))
        except Exception: continue
        res=d.get('result') if isinstance(d,dict) else None
        if not isinstance(res,dict): continue
        sha=(d.get('sha256') or '')[:8]
        for c in res.get('case_results',[]) or []:
            cf=c.get('case_file')
            if not cf or cf in EXCLUDE: continue
            try: score=float(c['total_score'])
            except Exception: continue
            cases[cf].append((score,p,sha,c))
            for det in c.get('detail',[]) or []:
                if not isinstance(det,dict) or 'cost' not in det: continue
                k=str(det.get('task_id_list') or '')
                cs=couriers_of(det.get('couriers'))
                if not k or not cs: continue
                key=(k,cs)
                old=rows[cf].get(key)
                cost=float(det['cost'])
                if old is None or cost<old[0]: rows[cf][key]=(cost,p,score)
    return cases,rows

def solve(cf,rowmap,limit_sec=3.0):
    # exact branch over known rows with incumbent as best historical score
    all_tasks=sorted({t for k,_ in rowmap for t in tasks_of(k)})
    ti={t:i for i,t in enumerate(all_tasks)}
    all_couriers=sorted({c for _k,cs in rowmap for c in cs})
    ci={c:i for i,c in enumerate(all_couriers)}
    opts=[]
    for (k,cs),(cost,p,score) in rowmap.items():
        tm=0
        ok=True
        for t in tasks_of(k):
            if t not in ti: ok=False; break
            tm|=1<<ti[t]
        if not ok or not tm: continue
        cm=0
        for c in cs: cm|=1<<ci[c]
        opts.append((tm,cm,cost,k,cs,p,score))
    by=[[] for _ in all_tasks]
    for o in opts:
        for i in range(len(all_tasks)):
            if o[0]>>i&1: by[i].append(o)
    for b in by: b.sort(key=lambda o:(o[2]/max(1,bin(o[0]).count('1')),o[2]))
    allmask=(1<<len(all_tasks))-1
    best=PEN*len(all_tasks); bestsel=[]; nodes=0; start=time.monotonic(); memo={}
    def choose(dec,cm):
        rem=allmask&~dec; bi=None; bo=None
        while rem:
            bit=rem&-rem; i=bit.bit_length()-1
            os=[o for o in by[i] if not(o[0]&dec) and not(o[1]&cm)]
            if bo is None or len(os)<len(bo): bi=i; bo=os
            if bo==[]: break
            rem^=bit
        return bi,bo or []
    def dfs(dec,cm,cost,sel):
        nonlocal best,bestsel,nodes
        nodes+=1
        if nodes>200000 or time.monotonic()-start>limit_sec: return
        if cost>=best-1e-9: return
        state=(dec,cm)
        old=memo.get(state)
        if old is not None and old<=cost+1e-9: return
        memo[state]=cost
        if dec==allmask:
            best=cost; bestsel=list(sel); return
        i,os=choose(dec,cm)
        if i is None:
            if cost<best: best=cost; bestsel=list(sel)
            return
        # cover first, abandon last
        for o in os[:40]:
            sel.append(o); dfs(dec|o[0],cm|o[1],cost+o[2],sel); sel.pop()
        dfs(dec|(1<<i),cm,cost+PEN,sel)
    dfs(0,0,0.0,[])
    cov=set()
    for o in bestsel: cov.update(tasks_of(o[3]))
    return best,len(cov),len(all_tasks),len(bestsel),nodes,time.monotonic()-start,bestsel

def main():
    cases,rows=collect()
    out=['# Non-Bottleneck Official Detail Recombination Audit','']
    for cf in sorted(cases):
        scores=Counter(round(x[0],4) for x in cases[cf])
        hist_best=min(x[0] for x in cases[cf])
        best,covered,n_tasks,n_rows,nodes,sec,sel=solve(cf,rows[cf])
        out += [f'## {cf}','',f'- historical best: `{hist_best:.4f}`',f'- unique known rows: `{len(rows[cf])}`',f'- exact/limited known-row recombination: `{best:.4f}` coverage `{covered}/{n_tasks}` rows `{n_rows}` nodes `{nodes}` time `{sec:.2f}s`',f'- delta vs historical best: `{best-hist_best:+.4f}`','']
        out.append('Score distribution: '+', '.join(f'`{s:.4f}`×{n}' for s,n in sorted(scores.items())[:10])); out.append('')
    Path('runs/non_bottleneck_case_audit_latest.md').write_text('\n'.join(out)+'\n')
    print('runs/non_bottleneck_case_audit_latest.md')
if __name__=='__main__': main()
