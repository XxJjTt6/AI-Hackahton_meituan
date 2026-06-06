import json, glob
CASE='low_willingness_seed501.txt'; TASKS=[f'T{i:04d}' for i in range(30)]; COURIERS=[f'C{i:03d}' for i in range(60)]
ti={t:i for i,t in enumerate(TASKS)}; ci={c:i for i,c in enumerate(COURIERS)}
cols={}
for f in glob.glob('runs/official_submit_*.json'):
    try:data=json.load(open(f)); rs=(data.get('result') or {}).get('case_results',[])
    except:continue
    for c in rs:
        if c.get('case_file')!=CASE: continue
        for d in c.get('detail',[]):
            tasks=tuple(d['task_id_list'].split(',')); cour=tuple(d['couriers'])
            if any(t not in ti for t in tasks) or any(x not in ci for x in cour): continue
            tm=0; cm=0
            for t in tasks: tm|=1<<ti[t]
            ok=True
            for x in cour:
                bit=1<<ci[x]
                if cm&bit: ok=False; break
                cm|=bit
            if not ok: continue
            sig=(d['task_id_list'],cour); old=cols.get(sig)
            if old is None or d['cost']<old[0]: cols[sig]=(float(d['cost']),tm,cm,d)
C=list(cols.values())
print('cols',len(C),'bundle',sum(1 for _,_,_,d in C if ',' in d['task_id_list']),'kdist',{})
# include skip penalty via objective; beam over columns sorted by savings
C.sort(key=lambda x:(100*x[1].bit_count()-x[0],-x[2].bit_count()), reverse=True)
for width in [1000,5000,20000,100000,300000]:
    states={(0,0):(0.0,())}; best=(3000,None,0,0)
    for idx,(cost,tm,cm,d) in enumerate(C):
        add=[]
        for (tmask,cmask),(val,path) in states.items():
            if tmask&tm or cmask&cm: continue
            nt=tmask|tm; nc=cmask|cm; nv=val+cost; obj=nv+100*(30-nt.bit_count())
            old=states.get((nt,nc))
            if old is None or nv<old[0]: add.append(((nt,nc),(nv,path+(idx,))))
            if obj<best[0]: best=(obj,path+(idx,),nt,nc)
        for k,v in add:
            old=states.get(k)
            if old is None or v[0]<old[0]: states[k]=v
        if len(states)>width*2:
            states=dict(sorted(states.items(), key=lambda kv:(kv[1][0]+100*(30-kv[0][0].bit_count()),-kv[0][0].bit_count(),kv[0][1].bit_count()))[:width])
    print('\nwidth',width,'best',round(best[0],4),'covered',best[2].bit_count(),'couriers',best[3].bit_count(),'groups',len(best[1] or ()))
    for i in (best[1] or ()):
        d=C[i][3]
        print(' ',d['task_id_list'],d['couriers'],d['cost'])
