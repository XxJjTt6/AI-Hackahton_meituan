import json, glob, random, math, time, collections
CASE='low_willingness_seed501.txt'; TASKS=[f'T{i:04d}' for i in range(30)]; COURIERS=[f'C{i:03d}' for i in range(60)]
ti={t:i for i,t in enumerate(TASKS)}; ci={c:i for i,c in enumerate(COURIERS)}
cols={}
for f in glob.glob('runs/official_submit_*.json'):
    try:data=json.load(open(f)); rs=(data.get('result') or {}).get('case_results',[])
    except Exception:continue
    for c in rs:
        if c.get('case_file')!=CASE:continue
        for d in c.get('detail',[]):
            tasks=tuple(d['task_id_list'].split(',')); cour=tuple(d['couriers'])
            if any(t not in ti for t in tasks) or any(x not in ci for x in cour):continue
            tm=0; cm=0
            for t in tasks: tm|=1<<ti[t]
            ok=True
            for x in cour:
                b=1<<ci[x]
                if cm&b:ok=False;break
                cm|=b
            if not ok:continue
            sig=(d['task_id_list'],cour)
            if sig not in cols or d['cost']<cols[sig][0]: cols[sig]=(float(d['cost']),tm,cm,d)
C=list(cols.values())
base=1799.9031
print('cols',len(C),'bundle',sum(1 for _,tm,_,_ in C if tm.bit_count()>1),'kdist',collections.Counter(cm.bit_count() for _,_,cm,_ in C),flush=True)

def greedy(lam_t,lam_c,noise=0.0):
    order=[]
    for idx,(cost,tm,cm,d) in enumerate(C):
        adj=cost-sum(lam_t[i] for i in range(30) if tm>>i&1)+sum(lam_c[i] for i in range(60) if cm>>i&1)
        if noise: adj+=random.random()*noise
        order.append((adj,idx))
    order.sort()
    usedt=usedc=0; path=[]; val=0
    for _,idx in order:
        cost,tm,cm,d=C[idx]
        if usedt&tm or usedc&cm:continue
        # require positive reduced-ish saving unless it covers currently uncovered cheaply
        path.append(idx); usedt|=tm; usedc|=cm; val+=cost
        if usedt.bit_count()==30:break
    obj=val+100*(30-usedt.bit_count())
    return obj,usedt,usedc,path
best=(base,None)
# deterministic sweeps: reward all tasks, penalize crowded couriers from low best observed columns lightly
for task_reward in [70,80,90,100,110,120,140]:
  for courier_penalty in [0,1,2,4,8,12,18]:
    obj,ut,uc,path=greedy([task_reward]*30,[courier_penalty]*60)
    if obj<best[0]: best=(obj,path); print('best sweep',obj,ut.bit_count(),uc.bit_count(),task_reward,courier_penalty,flush=True)
# subgradient-ish update
lam_t=[100.0]*30; lam_c=[0.0]*60
for it in range(300):
    obj,ut,uc,path=greedy(lam_t,lam_c,noise=0.001)
    if obj<best[0]: best=(obj,path); print('best iter',it,obj,ut.bit_count(),uc.bit_count(),flush=True)
    step=8.0/(1+it/40)
    for i in range(30):
        if ut>>i&1: lam_t[i]-=step*0.15
        else: lam_t[i]+=step
    for i in range(60):
        if uc>>i&1: lam_c[i]+=step*0.08
        else: lam_c[i]*=0.995
print('FINAL',best[0], 'delta',best[0]-base,flush=True)
if best[1]:
    for idx in best[1]:
        d=C[idx][3]; print(d['task_id_list'],d['couriers'],d['cost'])
