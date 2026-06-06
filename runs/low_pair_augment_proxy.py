# Local prototype: start from greedy top pairs, try alternating replacement augment on official_like_low_synth.
import sys,itertools,collections,time
sys.path.insert(0,'.')
import solver
from pathlib import Path
text=Path('runs/official_like_low_synth.txt').read_text()
rows=[]; tasks=set()
for i,line in enumerate(text.strip().splitlines()[1:]):
    k,c,sc,w=line.split('\t')[:4]; ts=tuple(k.split(','))
    if len(ts)==1:
        rows.append((k,ts,c,float(sc),float(w),i)); tasks.add(ts[0])
opts={}
for t in sorted(tasks):
    rs=[r for r in rows if r[1][0]==t]; arr=[]
    for a,b in itertools.combinations(rs,2):
        if a[2]==b[2]: continue
        arr.append((solver._group_expected_cost([a,b],1),t,(a[2],b[2])))
    arr.sort(key=lambda x:x[0]); opts[t]=arr[:12]
# greedy by regret
used=set(); sol={}
for t in sorted(tasks, key=lambda x: (opts[x][1][0]-opts[x][0][0]) if len(opts[x])>1 else 999, reverse=True):
    for c,_,cs in opts[t]:
        if cs[0] not in used and cs[1] not in used:
            sol[t]=(c,cs); used.update(cs); break
print('greedy tasks',len(sol),'cost',round(sum(v[0] for v in sol.values())+100*(len(tasks)-len(sol)),2),'unused_tasks',sorted(set(tasks)-set(sol)))
# local 2-task swap
improved=True
while improved:
    improved=False
    for a,b in itertools.combinations(sorted(tasks),2):
        old=0; free=set()
        for t in [a,b]:
            if t in sol: old+=sol[t][0]; free.update(sol[t][1])
            else: old+=100
        base_used=used-free
        best=(old,None)
        for oa in opts[a]:
            ca=oa[2]
            if ca[0] in base_used or ca[1] in base_used or ca[0]==ca[1]: continue
            for ob in opts[b]:
                cb=ob[2]
                if cb[0] in base_used or cb[1] in base_used or set(ca)&set(cb): continue
                val=oa[0]+ob[0]
                if val<best[0]-1e-9: best=(val,(oa,ob))
        if best[1]:
            for t in [a,b]:
                if t in sol:
                    for c in sol[t][1]: used.remove(c)
            for t,o in zip([a,b],best[1]): sol[t]=(o[0],o[2]); used.update(o[2])
            improved=True
            print('improve',a,b,'cost',round(sum(v[0] for v in sol.values())+100*(len(tasks)-len(sol)),2),flush=True)
            break
        if improved: break
print('final tasks',len(sol),'cost',round(sum(v[0] for v in sol.values())+100*(len(tasks)-len(sol)),2),'unused',sorted(set(tasks)-set(sol)))
