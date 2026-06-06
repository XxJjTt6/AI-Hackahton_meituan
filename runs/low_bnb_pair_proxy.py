import sys,itertools,time,math
sys.path.insert(0,'.')
import solver
from pathlib import Path
text=Path('runs/official_like_low_synth.txt').read_text()
rows=[]; tasks=set(); couriers=set()
for i,line in enumerate(text.strip().splitlines()[1:]):
    k,c,sc,w=line.split('\t')[:4]; ts=tuple(k.split(','))
    if len(ts)==1:
        r=(k,ts,c,float(sc),float(w),i); rows.append(r); tasks.add(ts[0]); couriers.add(c)
ci={c:i for i,c in enumerate(sorted(couriers))}
opts=[]
for t in sorted(tasks):
    rs=[r for r in rows if r[1][0]==t]
    pairs=[]
    for a,b in itertools.combinations(rs,2):
        cm=(1<<ci[a[2]])|(1<<ci[b[2]])
        pairs.append((solver._group_expected_cost([a,b],1),cm,t,(a[2],b[2])))
    pairs.sort(key=lambda x:x[0]); opts.append(pairs[:8])
order=sorted(range(len(opts)), key=lambda i: opts[i][0][0] if opts[i] else 1e9)
best=[1e9,None]; cur=[]; deadline=time.monotonic()+20
mins=[min((x[0] for x in opts[i]), default=100) for i in order]
suffix=[0]*(len(order)+1)
for i in range(len(order)-1,-1,-1): suffix[i]=suffix[i+1]+mins[i]
def dfs(pos,mask,cost):
    if time.monotonic()>deadline: return
    if cost+suffix[pos]>=best[0]: return
    if pos==len(order): best[0]=cost; best[1]=list(cur); print('best',best[0],flush=True); return
    i=order[pos]
    for c,cm,t,cs in opts[i]:
        if mask&cm: continue
        cur.append((t,cs,c)); dfs(pos+1,mask|cm,cost+c); cur.pop()
dfs(0,0,0.0)
print('final',best[0],'found',best[1] is not None)
if best[1]: print(best[1][:10])
