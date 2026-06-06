# Exact-ish low K=2 assignment on official-like low synth using min-cost flow over task slots and courier pairs is too large;
# this prototype uses DP over tasks with top pair options from rows.
import sys,itertools,time,collections
sys.path.insert(0,'.')
import solver
from pathlib import Path
text=Path('runs/official_like_low_synth.txt').read_text()
rows=[]; tasks=set(); couriers=set()
for i,line in enumerate(text.strip().splitlines()[1:]):
    k,c,sc,w=line.split('\t')[:4]; ts=tuple(k.split(','))
    if len(ts)==1:
        rows.append((k,ts,c,float(sc),float(w),i)); tasks.update(ts); couriers.add(c)
tasks=sorted(tasks); ci={c:i for i,c in enumerate(sorted(couriers))}
opts=[]
for t in tasks:
    rs=[r for r in rows if r[1][0]==t]
    pairs=[]
    for a,b in itertools.combinations(rs,2):
        if a[2]==b[2]: continue
        cost=solver._group_expected_cost([a,b],1)
        pairs.append((cost,t,(a[2],b[2]),(a,b)))
    pairs.sort(key=lambda x:x[0]); opts.append(pairs[:30])
states={0:(0.0,())}; width=50000; start=time.monotonic()
for tii,pairs in enumerate(opts):
    nxt={}
    for mask,(cost,sol) in states.items():
        for c,t,cs,ab in pairs:
            cm=(1<<ci[cs[0]])|(1<<ci[cs[1]])
            if mask&cm: continue
            nm=mask|cm; val=(cost+c, sol+((t,cs,c),))
            old=nxt.get(nm)
            if old is None or val[0]<old[0]: nxt[nm]=val
    states=dict(sorted(nxt.items(), key=lambda kv:kv[1][0])[:width])
    print('step',tii+1,'states',len(states),'best',round(min(v[0] for v in states.values()),2),flush=True)
best=min(states.values(), key=lambda x:x[0])
print('best cost',best[0],'time',time.monotonic()-start)
print(best[1][:10])
