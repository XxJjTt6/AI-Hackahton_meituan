import json, glob, collections, bisect, time
CASE='low_willingness_seed501.txt'; TASKS=[f'T{i:04d}' for i in range(30)]; COURIERS=[f'C{i:03d}' for i in range(60)]
ci={c:i for i,c in enumerate(COURIERS)}
opts=collections.defaultdict(dict)
inc_score=1799.9031
for f in glob.glob('runs/official_submit_*.json'):
    try:data=json.load(open(f)); rs=(data.get('result') or {}).get('case_results',[])
    except:continue
    for c in rs:
        if c.get('case_file')!=CASE:continue
        for d in c.get('detail',[]):
            if ',' in d['task_id_list']: continue
            t=d['task_id_list']; cm=0; ok=True
            for cc in d['couriers']:
                if cc not in ci: ok=False; break
                bit=1<<ci[cc]
                if cm&bit: ok=False; break
                cm|=bit
            if not ok: continue
            sig=tuple(d['couriers']); old=opts[t].get(sig)
            if old is None or d['cost']<old[0]: opts[t][sig]=(float(d['cost']),cm,d)
# keep top options per task by cost plus incumbent-ish K2s; top 10 enough for exact observed test
options=[]
for t in TASKS:
    arr=sorted(opts[t].values(), key=lambda x:(x[0], x[1].bit_count()))[:14]
    options.append(arr)
    print(t,'n',len(arr),'best',[(round(x[0],2),x[1].bit_count(),x[2]['couriers']) for x in arr[:5]],flush=True)

def enum_half(task_options, limit_per_layer=250000):
    states=[(0.0,0,[])]
    for arr in task_options:
        ns=[]
        for val,mask,path in states:
            for cost,cm,d in arr:
                if mask&cm: continue
                ns.append((val+cost,mask|cm,path+[d]))
        ns.sort(key=lambda x:(x[0],x[1].bit_count()))
        out=[]; seen=set()
        for st in ns:
            if st[1] in seen: continue
            seen.add(st[1]); out.append(st)
            if len(out)>=limit_per_layer: break
        states=out
        print(' layer',len(states),states[0][0],flush=True)
    return states
start=time.monotonic(); left=enum_half(options[:15]); right=enum_half(options[15:]); print('enum done',len(left),len(right),'time',time.monotonic()-start,flush=True)
# Sort right by cost; scan feasible best with prefix not easy due masks, but 250k*? use buckets by cost and early break.
right.sort(key=lambda x:x[0]); left.sort(key=lambda x:x[0]); best=(inc_score,None,None)
for Lcap,Rcap in [(2000,20000),(10000,50000),(40000,100000),(len(left),len(right))]:
    print('scan caps',Lcap,Rcap,flush=True)
    for li,(lv,lm,lp) in enumerate(left[:Lcap]):
        if lv+right[0][0]>=best[0]: continue
        for rv,rm,rp in right[:Rcap]:
            ss=lv+rv
            if ss>=best[0]: break
            if lm&rm: continue
            best=(ss,lp,rp); print('best',best[0], 'li',li,'caps',Lcap,Rcap,flush=True); break
print('FINAL',best[0], 'delta',best[0]-inc_score, 'time',time.monotonic()-start,flush=True)
if best[1]:
    for d in best[1]+best[2]: print(d['task_id_list'],d['couriers'],d['cost'])
