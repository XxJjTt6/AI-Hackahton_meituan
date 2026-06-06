#!/usr/bin/env python3
import json, glob, itertools, collections
def pc(x): return bin(x).count('1')

def load_case(path, name):
    d=json.load(open(path))
    for c in d.get('result',{}).get('case_results',[]):
        if c.get('case_file')==name:
            return c, d.get('sha256','')[:8], path
    return None, None, None

def mask_tasks(task_key): return frozenset(task_key.split(','))
def mask_couriers(cs): return frozenset(cs)

for name in ['high_noise_seed601.txt','large_seed301.txt','large_seed302.txt','medium_seed201.txt']:
    groups=[]
    baseline=None
    seen=set()
    for p in glob.glob('runs/official_submit_*.json'):
        c,sha,path=load_case(p,name)
        if not c: continue
        if sha=='8ee7a12d' or abs(c['total_score']-min(c['total_score'], 1e9))<0: pass
        if baseline is None or c['total_score']<baseline['total_score']:
            baseline=c
        for r in c.get('detail',[]):
            key=(r['task_id_list'], tuple(r['couriers']))
            if key in seen: continue
            seen.add(key)
            groups.append(dict(task_key=r['task_id_list'], couriers=tuple(r['couriers']), tasks=mask_tasks(r['task_id_list']), cs=mask_couriers(r['couriers']), exp=r['cost'], src=sha))
    if not baseline: continue
    all_tasks=set()
    for r in baseline['detail']:
        all_tasks |= mask_tasks(r['task_id_list'])
    # DP choose disjoint groups minimizing sum expected_score + official-like unassigned penalty 100 each.
    task_list=sorted(all_tasks); tid={t:i for i,t in enumerate(task_list)}
    cols=[]
    for g in groups:
        if not g['tasks'] <= all_tasks: continue
        tm=0
        for t in g['tasks']: tm|=1<<tid[t]
        cols.append((g['exp'],tm,g['cs'],g))
    # Beam by expected score and coverage; courier conflicts tracked as frozenset.
    states={(0,frozenset()):(0.0,[])}
    for exp,tm,cs,g in sorted(cols,key=lambda x:(x[0]/len(x[3]['tasks']), x[0])):
        new=[]
        for (m,used),(cost,sol) in list(states.items()):
            if m&tm or used&cs: continue
            nm=m|tm; nu=used|cs; nc=cost+exp
            old=states.get((nm,nu))
            if old is None or nc<old[0]-1e-9: new.append(((nm,nu),(nc,sol+[g])))
        for k,v in new: states[k]=v
        if len(states)>4000:
            items=sorted(states.items(),key=lambda kv:(kv[1][0]+100*(len(task_list)-pc(kv[0][0])), -pc(kv[0][0])))[:2000]
            states=dict(items)
    best=min(states.values(), key=lambda v:v[0]+100*(len(task_list)-sum(len(g['tasks']) for g in v[1])))
    cov=sum(len(g['tasks']) for g in best[1]); proxy=best[0]+100*(len(task_list)-cov)
    print('\n',name,'baseline',baseline['total_score'],'baseline_sum_cost',round(sum(r['cost'] for r in baseline['detail']),4),'hybrid_exp_proxy',round(proxy,4),'cov',cov,'groups',len(best[1]),'pool',len(groups))
    if proxy < sum(r['cost'] for r in baseline['detail'])-1e-6:
        for g in best[1]: print(' ',g['task_key'],list(g['couriers']),g['exp'],g['src'])
