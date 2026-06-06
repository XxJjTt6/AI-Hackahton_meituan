import json,glob,os,math
cols={}
for f in glob.glob('runs/official_submit_*.json')+glob.glob('runs/official_result_*.json'):
    try:d=json.load(open(f)); r=d.get('result') or d
    except Exception:continue
    for case in r.get('case_results') or []:
        if case.get('case_file')!='scarce_couriers_seed401.txt':continue
        for x in case.get('detail') or []:
            ts=tuple(sorted(x['task_id_list'].split(',')))
            cs=tuple(x['couriers'])
            cost=float(x['cost'])
            key=(ts,cs)
            if key not in cols or cost<cols[key][0]: cols[key]=(cost,x.get('p_complete'),x.get('expected_score'),os.path.basename(f))
T={f'T{i:04d}':i for i in range(40)}; C={f'C{i:03d}':i for i in range(40)}
items=[]
for (ts,cs),(cost,p,e,f) in cols.items():
    if any(t not in T for t in ts) or any(c not in C for c in cs): continue
    tm=sum(1<<T[t] for t in ts); cm=sum(1<<C[c] for c in cs); sav=100*len(ts)-cost
    if sav>0: items.append((sav,cost,tm,cm,ts,cs,p,e,f))
print('unique cols',len(cols),'positive',len(items))
# exact branch and bound by uncovered task with optimistic bound
bytask={i:[] for i in range(40)}
for idx,it in enumerate(items):
    for t in range(40):
        if it[2]>>t&1: bytask[t].append(idx)
for t in bytask: bytask[t].sort(key=lambda i:items[i][0], reverse=True)
best=(0,[])
# optimistic task-level bound: at most 100 saving per uncovered task, loose but safe
def dfs(tm,cm,sav,pick):
    global best
    if sav+100*(40-tm.bit_count())<=best[0]+1e-9:return
    # update with current partial: uncovered tasks pay penalty
    if sav>best[0]:best=(sav,pick[:])
    # choose uncovered task with fewest feasible positive columns; also allow skip it
    miss=[t for t in range(40) if not (tm>>t)&1]
    if not miss:return
    chosen=None; feas=None
    for t in miss:
        fs=[i for i in bytask[t] if not(items[i][2]&tm or items[i][3]&cm)]
        if chosen is None or len(fs)<len(feas): chosen=t; feas=fs
    # skip chosen task (pay penalty implicitly by not gaining savings)
    dfs(tm| (1<<chosen), cm, sav, pick)
    for i in feas[:80]:
        it=items[i]
        pick.append(i);dfs(tm|it[2],cm|it[3],sav+it[0],pick);pick.pop()
dfs(0,0,0,[])
print('best score from revealed',4000-best[0],'savings',best[0],'cols',len(best[1]),'covered_tasks',sum((items[i][2]).bit_count() for i in best[1]))
for i in best[1]:
    sav,cost,tm,cm,ts,cs,p,e,f=items[i]
    print(','.join(ts), list(cs), 'cost',round(cost,4),'sav',round(sav,4),'from',f)
# baseline cols exact if present
base=[(('T0000','T0027'),('C005',)),(('T0001','T0035'),('C018',)),(('T0002','T0038'),('C009',)),(('T0003','T0024'),('C012',)),(('T0004','T0018'),('C007',)),(('T0005','T0036'),('C019',)),(('T0006','T0030'),('C003',)),(('T0007','T0008'),('C001',)),(('T0009','T0011'),('C014',)),(('T0010','T0029'),('C004',)),(('T0012','T0019'),('C010',)),(('T0013','T0039'),('C013',)),(('T0014','T0031'),('C008',)),(('T0015','T0034'),('C015',)),(('T0016',),('C000',)),(('T0017','T0032'),('C002',)),(('T0020','T0023'),('C016',)),(('T0021','T0026'),('C017',)),(('T0022','T0037'),('C011',)),(('T0025','T0028'),('C006',))]
print('baseline known')
s=0;cov=set()
for key in base:
    v=cols.get(key)
    if v:s+=v[0]; cov.update(key[0])
    else: print('missing',key)
print('baseline calc',s+100*(40-len(cov)), 'cost',s,'cov',len(cov))
