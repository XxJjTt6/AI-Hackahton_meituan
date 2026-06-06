import json, glob, os, itertools
from collections import defaultdict

def tasks_of(k): return tuple(k.split(','))

def solve_case(cols, total_tasks):
    tasks=sorted({t for k,_,_,_,_ in cols for t in tasks_of(k)})
    # add dummy unassigned columns per task
    for t in tasks:
        cols.append((t, (), 100.0, 'dummy', None))
    tid={t:i for i,t in enumerate(tasks)}
    cid={c:i for i,c in enumerate(sorted({c for _,cs,_,_,_ in cols for c in cs}))}
    items=[]
    for k,cs,cost,src,detail in cols:
        tm=0
        ok=True
        for t in tasks_of(k):
            if t not in tid: ok=False; break
            tm |= 1<<tid[t]
        cm=0
        for c in cs: cm |= 1<<cid[c]
        if ok: items.append((tm,cm,cost,k,cs,src,detail))
    n=len(tasks); full=(1<<n)-1
    by_first=defaultdict(list)
    for it in items:
        tm=it[0]
        if tm: by_first[(tm & -tm).bit_length()-1].append(it)
    for v in by_first.values(): v.sort(key=lambda x:x[2])
    best=[float('inf'), None]
    cur=[]
    def rec(mask, cmask, cost):
        if cost>=best[0]-1e-9: return
        if mask==full:
            best[0]=cost; best[1]=list(cur); return
        rem=full^mask; i=(rem & -rem).bit_length()-1
        for it in by_first.get(i,[]):
            tm,cm,c,*rest=it
            if tm&mask or cm&cmask: continue
            cur.append(it); rec(mask|tm, cmask|cm, cost+c); cur.pop()
    rec(0,0,0.0)
    return best, tasks

cases=defaultdict(dict)
for p in glob.glob('runs/official_submit_*.json'):
    try: j=json.load(open(p))['result']
    except Exception: continue
    tag=os.path.basename(p).replace('official_submit_','').replace('.json','')
    for cr in j.get('case_results',[]):
        case=cr['case_file']
        for d in cr.get('detail',[]):
            k=d['task_id_list']; cs=tuple(d['couriers']); cost=float(d['cost'])
            key=(k,cs)
            old=cases[case].get(key)
            if old is None or cost<old[0]-1e-9:
                cases[case][key]=(cost,tag,d)

for case, mp in sorted(cases.items()):
    cols=[(k,cs,cost,src,d) for (k,cs),(cost,src,d) in mp.items()]
    (score, sol), tasks=solve_case(cols, None)
    latest=json.load(open('runs/official_submit_20260519_154154_95581ea7.json'))['result']
    cur=next(cr for cr in latest['case_results'] if cr['case_file']==case)
    cur_score=float(cur['total_score'])
    print('\nCASE',case,'cur',cur_score,'ensemble',round(score,4),'delta',round(score-cur_score,4),'cols',len(cols))
    if score < cur_score-1e-6:
        for it in sorted(sol, key=lambda x:x[3]):
            tm,cm,c,k,cs,src,d=it
            if cs:
                print(' ',k, list(cs), round(c,4), src)
