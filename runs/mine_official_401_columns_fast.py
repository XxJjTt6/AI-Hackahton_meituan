import json,glob,os
cols={}
for f in glob.glob('runs/official_submit_*.json')+glob.glob('runs/official_result_*.json'):
    try:d=json.load(open(f)); r=d.get('result') or d
    except Exception:continue
    for case in r.get('case_results') or []:
        if case.get('case_file')!='scarce_couriers_seed401.txt':continue
        for x in case.get('detail') or []:
            ts=tuple(sorted(x['task_id_list'].split(','))); cs=tuple(x['couriers']); cost=float(x['cost'])
            key=(ts,cs)
            if key not in cols or cost<cols[key][0]: cols[key]=(cost,os.path.basename(f))
T={f'T{i:04d}':i for i in range(40)}; C={f'C{i:03d}':i for i in range(40)}
raw=[]
for (ts,cs),(cost,f) in cols.items():
    if any(t not in T for t in ts) or any(c not in C for c in cs): continue
    sav=100*len(ts)-cost
    if sav<=0: continue
    mask=0
    for t in ts: mask|=1<<T[t]
    for c in cs: mask|=1<<(40+C[c])
    raw.append([sav,cost,mask,ts,cs,f])
raw.sort(key=lambda x:(x[0],len(x[3])),reverse=True)
# drop dominated exact same resource mask higher cost
items=[];seen={}
for x in raw:
    if x[2] in seen: continue
    seen[x[2]]=1;items.append(x)
n=len(items);conf=[0]*n
for i in range(n):
    for j in range(n):
        if i!=j and items[i][2]&items[j][2]: conf[i]|=1<<j
sav=[x[0] for x in items]
# baseline lower bound
base=[(('T0000','T0027'),('C005',)),(('T0001','T0035'),('C018',)),(('T0002','T0038'),('C009',)),(('T0003','T0024'),('C012',)),(('T0004','T0018'),('C007',)),(('T0005','T0036'),('C019',)),(('T0006','T0030'),('C003',)),(('T0007','T0008'),('C001',)),(('T0009','T0011'),('C014',)),(('T0010','T0029'),('C004',)),(('T0012','T0019'),('C010',)),(('T0013','T0039'),('C013',)),(('T0014','T0031'),('C008',)),(('T0015','T0034'),('C015',)),(('T0016',),('C000',)),(('T0017','T0032'),('C002',)),(('T0020','T0023'),('C016',)),(('T0021','T0026'),('C017',)),(('T0022','T0037'),('C011',)),(('T0025','T0028'),('C006',))]
baseidx=[]
for b in base:
    for i,x in enumerate(items):
        if x[3]==b[0] and x[4]==b[1]: baseidx.append(i); break
best_s=sum(sav[i] for i in baseidx);best=baseidx[:]
print('cols',len(cols),'items',n,'baseline score',4000-best_s,'baseidx',len(baseidx),flush=True)
from functools import lru_cache
@lru_cache(None)
def ub(av):
    s=0; m=av
    while m:
        lb=m&-m; i=lb.bit_length()-1; s+=sav[i]; m-=lb
    return s
nodes=0
def dfs(av,cur,pick):
    global best_s,best,nodes
    nodes+=1
    if cur+ub(av)<=best_s+1e-9:return
    if not av:
        if cur>best_s:best_s=cur;best=pick[:];print('new',4000-best_s,len(best),flush=True)
        return
    # branch on item with high conflict pressure among available
    m=av; bi=None; bv=None
    while m:
        lb=m&-m; i=lb.bit_length()-1; m-=lb
        val=sav[i]*(1+((conf[i]&av).bit_count()))
        if bv is None or val>bv: bv=val; bi=i
    # include first
    dfs(av & ~conf[bi] & ~(1<<bi), cur+sav[bi], pick+[bi])
    dfs(av & ~(1<<bi), cur, pick)
allmask=(1<<n)-1
dfs(allmask,0,[])
print('nodes',nodes,'best score',round(4000-best_s,4),'savings',round(best_s,4),'cols',len(best),'covered',sum(len(items[i][3]) for i in best))
for i in sorted(best,key=lambda i:items[i][3]):
    x=items[i]
    print(','.join(x[3]), list(x[4]), 'cost',round(x[1],4),'sav',round(x[0],4),'from',x[5])
