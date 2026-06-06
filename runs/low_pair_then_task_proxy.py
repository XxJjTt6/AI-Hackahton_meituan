# Prototype: pair couriers greedily by complementarity, then assign pairs to tasks.
import sys,itertools,collections,math
sys.path.insert(0,'.')
import solver
from pathlib import Path
text=Path('runs/official_like_low_synth.txt').read_text()
rows=[]; tasks=set(); couriers=set(); bytc={}
for i,line in enumerate(text.strip().splitlines()[1:]):
    k,c,sc,w=line.split('\t')[:4]; ts=tuple(k.split(','))
    if len(ts)==1:
        r=(k,ts,c,float(sc),float(w),i); rows.append(r); tasks.add(ts[0]); couriers.add(c); bytc[(ts[0],c)]=r
tasks=sorted(tasks); couriers=sorted(couriers)
# pair score = best task cost for pair
paircost=[]
for a,b in itertools.combinations(couriers,2):
    vals=[]
    for t in tasks:
        if (t,a) in bytc and (t,b) in bytc:
            vals.append(solver._group_expected_cost([bytc[(t,a)],bytc[(t,b)]],1))
    if vals: paircost.append((sum(sorted(vals)[:3])/min(3,len(vals)),a,b))
paircost.sort()
used=set(); pairs=[]
for _,a,b in paircost:
    if a not in used and b not in used:
        pairs.append((a,b)); used.add(a); used.add(b)
print('pairs',len(pairs),'unused',len(couriers)-len(used))
# assign pairs to tasks greedily by cost
usedp=set(); total=0; assigned=[]
for t in tasks:
    best=None
    for i,(a,b) in enumerate(pairs):
        if i in usedp or (t,a) not in bytc or (t,b) not in bytc: continue
        c=solver._group_expected_cost([bytc[(t,a)],bytc[(t,b)]],1)
        if best is None or c<best[0]: best=(c,i,a,b)
    if best:
        total+=best[0]; usedp.add(best[1]); assigned.append((t,best[2:],best[0]))
    else: total+=100
print('assigned',len(assigned),'cost',round(total,2),'first',assigned[:8])
