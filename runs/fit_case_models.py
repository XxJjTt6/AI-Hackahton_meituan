import json,glob,collections
allrows=collections.defaultdict(list)
for p in glob.glob('runs/official_submit_*.json'):
    try: j=json.load(open(p))['result']
    except Exception: continue
    for cr in j.get('case_results',[]):
        for d in cr.get('detail',[]):
            t=len(d['task_id_list'].split(',')); k=len(d['couriers']); pc=float(d['p_complete']); exp=float(d['expected_score']); cost=float(d['cost'])
            allrows[cr['case_file']].append(([exp,(1-pc)*100*t,t,k,1.0],cost))
def fit(rows):
    m=5; A=[[0.0]*m for _ in range(m)]; b=[0.0]*m
    for x,y in rows:
        for i in range(m):
            b[i]+=x[i]*y
            for j in range(m): A[i][j]+=x[i]*x[j]
    ridge=1e-8
    for i in range(m): A[i][i]+=ridge
    for i in range(m):
        piv=max(range(i,m), key=lambda r: abs(A[r][i])); A[i],A[piv]=A[piv],A[i]; b[i],b[piv]=b[piv],b[i]
        div=A[i][i]
        if abs(div)<1e-10: return None
        for j in range(i,m): A[i][j]/=div
        b[i]/=div
        for r in range(m):
            if r==i: continue
            fac=A[r][i]
            for j in range(i,m): A[r][j]-=fac*A[i][j]
            b[r]-=fac*b[i]
    errs=[abs(sum(c*v for c,v in zip(b,x))-y) for x,y in rows]
    return b, sum(errs)/len(errs), (sum(e*e for e in errs)/len(errs))**0.5, len(rows)
for case,rows in sorted(allrows.items()):
    got=fit(rows)
    if got:
        c,mae,rmse,n=got
        print(case,'n',n,'mae',round(mae,4),'coef',[round(x,5) for x in c])
