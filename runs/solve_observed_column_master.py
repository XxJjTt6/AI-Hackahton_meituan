#!/usr/bin/env python3
from __future__ import annotations
import argparse, glob, json


def collect(case_file):
    max_task = -1
    columns = {}
    best_path = 'runs/official_submit_20260520_132026_70222083.json'
    best_case = None
    for path in glob.glob('runs/official_submit_*.json'):
        try:
            d=json.load(open(path)); r=d.get('result') or {}
            for case in r.get('case_results',[]):
                if case.get('case_file') != case_file: continue
                if path == best_path:
                    best_case = case
                for g in case.get('detail',[]):
                    tasks=tuple(g['task_id_list'].split(',')); couriers=tuple(g['couriers'])
                    for t in tasks:
                        if t.startswith('T') and t[1:].isdigit(): max_task=max(max_task,int(t[1:]))
                    sig=(g['task_id_list'],couriers)
                    cost=float(g['cost'])
                    if sig not in columns or cost<columns[sig]['cost']:
                        columns[sig]={'task_key':g['task_id_list'],'tasks':tasks,'couriers':couriers,'cost':cost}
        except Exception: pass
    all_tasks=[f'T{i:04d}' for i in range(max_task+1)]
    task_index={t:i for i,t in enumerate(all_tasks)}
    all_couriers=sorted({c for col in columns.values() for c in col['couriers']})
    courier_index={c:i for i,c in enumerate(all_couriers)}
    cols=[]
    for col in columns.values():
        tm=0; cm=0; ok=True
        for t in col['tasks']:
            if t not in task_index: ok=False; break
            tm |= 1<<task_index[t]
        for c in col['couriers']:
            cm |= 1<<courier_index[c]
        if ok:
            saving=100*len(col['tasks'])-col['cost']
            cols.append((saving, col['cost'], tm, cm, col))
    cols.sort(reverse=True, key=lambda x:(x[0]/max(1,len(x[4]['tasks'])), x[0], -x[1]))
    return cols, all_tasks, best_case


def state_from_case(best_case, task_index, courier_index):
    if best_case is None:
        return None
    cost=0.0; tm=0; cm=0; path=[]
    for g in best_case.get('detail',[]):
        c={'task_key':g['task_id_list'],'tasks':tuple(g['task_id_list'].split(',')),'couriers':tuple(g['couriers']),'cost':float(g['cost'])}
        for t in c['tasks']: tm |= 1<<task_index[t]
        for co in c['couriers']: cm |= 1<<courier_index[co]
        cost += c['cost']; path.append(c)
    return (cost,tm,cm,path)

def solve(cols, n_tasks, beam=100000, incumbent=None):
    states=[(0.0,0,0,[])]
    best=(100*n_tasks,0,0,[])
    if incumbent is not None:
        states.append(incumbent); best=incumbent
    for saving,cost,tm,cm,col in cols:
        new=[]
        for sc,st,cu,path in states:
            if st&tm or cu&cm: continue
            ns=(sc+cost, st|tm, cu|cm, path+[col])
            new.append(ns)
            total=ns[0]+100*(n_tasks-ns[1].bit_count())
            btotal=best[0]+100*(n_tasks-best[1].bit_count())
            if total<btotal-1e-9 or (abs(total-btotal)<1e-9 and ns[1].bit_count()>best[1].bit_count()): best=ns
        if new:
            states.extend(new)
            states.sort(key=lambda s:(s[0]+100*(n_tasks-s[1].bit_count()), -s[1].bit_count(), s[2].bit_count()))
            out=[]; seen=set()
            for st in states:
                key=(st[1],st[2])
                if key in seen: continue
                seen.add(key); out.append(st)
                if len(out)>=beam: break
            states=out
    return best


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('case_file'); ap.add_argument('--beam',type=int,default=100000)
    a=ap.parse_args(); cols,tasks,best_case=collect(a.case_file)
    task_index={t:i for i,t in enumerate(tasks)}
    couriers=sorted({co for _,_,_,_,col in cols for co in col['couriers']})
    courier_index={co:i for i,co in enumerate(couriers)}
    incumbent=state_from_case(best_case, task_index, courier_index)
    best=solve(cols,len(tasks),a.beam,incumbent)
    total=best[0]+100*(len(tasks)-best[1].bit_count())
    missing=[t for i,t in enumerate(tasks) if not ((best[1]>>i)&1)]
    print('case',a.case_file,'cols',len(cols),'tasks',len(tasks),'total',round(total,4),'group_cost',round(best[0],4),'covered',best[1].bit_count(),'missing',missing,'groups',len(best[3]))
    for col in sorted(best[3], key=lambda c:c['task_key']): print(col['task_key'],list(col['couriers']),col['cost'])
if __name__=='__main__': main()
