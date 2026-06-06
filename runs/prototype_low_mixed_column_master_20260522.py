import importlib.util, pathlib, itertools, time, json, argparse
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('s',ROOT/'solver.py'); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
def parse(text):
    lines=text.strip().splitlines(); st=1 if lines and lines[0].startswith('task') else 0; C=[]; B=set()
    for i,l in enumerate(lines[st:]):
        p=l.split('\t')
        if len(p)<4: continue
        k,c,sc,w=p[:4]; ts=tuple(x.strip() for x in k.split(',') if x.strip())
        C.append((k,ts,c,float(sc),float(w),i)); B.update(ts)
    return C,sorted(B)
def to_masks(C,tasks):
    ti={t:i for i,t in enumerate(tasks)}; ci={c:i for i,c in enumerate(sorted({r[2] for r in C}))}; return ti,ci
def result_cols(out,C,tasks,ti,ci):
    row={(r[0],r[2]):r for r in C}; cols=[]
    for k,ls in out:
        rows=[row.get((k,c)) for c in ls]; rows=[r for r in rows if r]
        if not rows: continue
        tm=0; cm=0
        for t in rows[0][1]: tm|=1<<ti[t]
        for r in rows: cm|=1<<ci[r[2]]
        cost=s._group_expected_cost(rows,len(rows[0][1])); cols.append((cost,tm,cm,k,tuple(r[2] for r in rows),tuple(rows),'inc'))
    return cols
def build_cols(C,tasks,ti,ci,top_single=12,top_bundle=8,keep_single=45,keep_bundle=25):
    by={}; cols=[]
    for r in s._canonical_candidates(C): by.setdefault(r[0],[]).append(r)
    for key,rows0 in by.items():
        tc=len(rows0[0][1]); tm=0
        if tc>2: continue
        for t in rows0[0][1]: tm|=1<<ti[t]
        top=top_single if tc==1 else top_bundle; keep=keep_single if tc==1 else keep_bundle; maxk=4 if tc==1 else 3
        seed=[]; seen=set()
        for order in [lambda r:(s._group_expected_cost([r],tc),-r[4],r[5]), lambda r:(-r[4],r[3],r[5]), lambda r:(r[3]/max(r[4],.01),r[5])]:
            for r in sorted(rows0,key=order)[:top]:
                if r[2] not in seen: seen.add(r[2]); seed.append(r)
        opts=[]
        for k in range(1,min(maxk,len(seed))+1):
            for comb in itertools.combinations(seed,k):
                cm=0
                for r in comb: cm|=1<<ci[r[2]]
                cost=s._group_expected_cost(comb,tc)
                # keep columns that beat leaving tasks uncovered, plus some bundle bridges
                if cost<100*tc or tc==2:
                    opts.append((cost,tm,cm,key,tuple(r[2] for r in comb),tuple(comb),'single' if tc==1 else 'bundle'))
        opts.sort(key=lambda x:(x[0]-100*tc, x[0], len(x[4])))
        cols.extend(opts[:keep])
    return cols
def beam(cols,n,inc_cost,deadline,width=60000,slack=30):
    cols=sorted(cols,key=lambda x:(x[0]-100*x[1].bit_count(),x[0],-x[1].bit_count()))
    states={(0,0):(0.0,())}; best=(inc_cost,None)
    for idx,col in enumerate(cols):
        if time.monotonic()>deadline-.05: break
        cost,tm,cm,*_=col; add=[]
        for (tmask,cmask),(val,path) in states.items():
            if tmask&tm or cmask&cm: continue
            nt=tmask|tm; nc=cmask|cm; nv=val+cost; obj=nv+100*(n-nt.bit_count())
            if obj>inc_cost+slack: continue
            old=states.get((nt,nc))
            if old is None or nv<old[0]-1e-9: add.append(((nt,nc),(nv,path+(idx,))))
            if obj<best[0]-1e-9: best=(obj,path+(idx,))
        for k,v in add:
            old=states.get(k)
            if old is None or v[0]<old[0]-1e-9: states[k]=v
        if len(states)>width*2:
            states=dict(sorted(states.items(),key=lambda kv:(kv[1][0]+100*(n-kv[0][0].bit_count()),-kv[0][0].bit_count(),kv[0][1].bit_count()))[:width])
    return best
def out(cols,path):
    if path is None: return None
    return [(cols[i][3],list(cols[i][4])) for i in path]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--seconds',type=float,default=20); ap.add_argument('--width',type=int,default=80000); ap.add_argument('--slack',type=float,default=50)
    a=ap.parse_args(); text=pathlib.Path(a.input).read_text(); C,tasks=parse(text); inc=s.solve(text); ic=s._solution_expected_cost(inc,C,set(tasks)); ti,ci=to_masks(C,tasks); cols=result_cols(inc,C,tasks,ti,ci)+build_cols(C,tasks,ti,ci)
    start=time.monotonic(); best,path=beam(cols,len(tasks),ic,time.monotonic()+a.seconds,a.width,a.slack); res=out(cols,path) or inc; rc=s._solution_expected_cost(res,C,set(tasks))
    print(json.dumps({'case':pathlib.Path(a.input).name,'inc':ic,'master':rc,'delta':rc-ic,'cols':len(cols),'groups':len(res),'time':time.monotonic()-start},ensure_ascii=False))
    if rc<ic-1e-9: print(res)
if __name__=='__main__': main()
