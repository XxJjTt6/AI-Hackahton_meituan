#!/usr/bin/env python3
import sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval

def covered(res, rows):
    lut={(r[0],r[2]):r for r in rows}
    out=set()
    for k,cs in res:
        for c in cs:
            r=lut.get((k,c))
            if r:
                out.update(r[1]); break
    return out

def selected(mod,res,rows):
    row_map={(r[0],r[2]):r for r in rows}
    return mod._result_to_selected(res,row_map)

def signature(res):
    return hashlib.sha256('\n'.join(f'{k}:{",".join(cs)}' for k,cs in res).encode()).hexdigest()[:12]

def run(path,scale):
    mod=proxy_eval.load(ROOT/path)
    text=proxy_eval.make_low(scale)
    rows,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
    t0=time.monotonic(); base=mod.solve(text); dt=time.monotonic()-t0
    base_cost=mod._solution_expected_cost(base,rows,T)
    sel=selected(mod,base,rows)
    groups=[]
    for k,g in sel.items():
        if not g: continue
        tasks=tuple(g[0][1]); c=mod._group_expected_cost(g,len(tasks))
        groups.append((c/max(1,len(tasks)),c,k,tasks,len(g),[r[2] for r in g]))
    groups.sort(reverse=True)
    print('case',scale,'base',round(base_cost,6),'time',round(dt,3),'sig',signature(base),'cov',len(covered(base,rows)),'groups',len(base), flush=True)
    print('worst groups:', flush=True)
    for g in groups[:12]: print(' ',g, flush=True)
    # Try one-window repairs around worst group only; record strict improvements.
    adj=mod._task_adjacency(rows)
    best=(base_cost,base,'base')
    for _,_,key,tasks0,_,_ in groups[:10]:
        win=set(tasks0)
        for t in tasks0:
            for nb in sorted(adj.get(t,()))[:8]:
                if len(win)<10: win.add(nb)
        s=selected(mod,base,rows)
        cand=mod._repair_task_window(s,rows,T,win,time.monotonic()+0.18,top_riders_per_task_key=10,max_k=4,option_limit=80)
        if cand:
            cost=mod._solution_expected_cost(cand,rows,T)
            if cost<best[0]-1e-9: best=(cost,cand,'repair '+','.join(tasks0))
    print('best_window',round(best[0],6),best[2],'delta',round(best[0]-base_cost,6),'sig',signature(best[1]), flush=True)

if __name__=='__main__':
    p=sys.argv[1] if len(sys.argv)>1 else 'solver.py'
    for sc in (.25,): run(p,sc)
