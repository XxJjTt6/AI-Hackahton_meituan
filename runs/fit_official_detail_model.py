import json, glob
rows=[]
for p in glob.glob('runs/official_submit_*.json'):
    try:
        j=json.load(open(p))['result']
    except Exception:
        continue
    for cr in j.get('case_results',[]):
        for d in cr.get('detail',[]):
            tasks=len(d['task_id_list'].split(','))
            couriers=len(d['couriers'])
            p_complete=float(d['p_complete'])
            expected=float(d['expected_score'])
            cost=float(d['cost'])
            rows.append((cr['case_file'],tasks,couriers,p_complete,expected,cost))
print('rows',len(rows))
features=[]; y=[]
for case,tasks,couriers,p_complete,expected,cost in rows:
    features.append([expected,(1-p_complete)*100*tasks,tasks,couriers,1.0])
    y.append(cost)
m=len(features[0])
A=[[0.0]*m for _ in range(m)]
b=[0.0]*m
for x,yy in zip(features,y):
    for i in range(m):
        b[i]+=x[i]*yy
        for j in range(m):
            A[i][j]+=x[i]*x[j]
for i in range(m):
    pivot=max(range(i,m), key=lambda r: abs(A[r][i]))
    A[i],A[pivot]=A[pivot],A[i]
    b[i],b[pivot]=b[pivot],b[i]
    div=A[i][i]
    if abs(div)<1e-12:
        raise SystemExit('singular normal equation')
    for j in range(i,m):
        A[i][j]/=div
    b[i]/=div
    for r in range(m):
        if r==i:
            continue
        fac=A[r][i]
        for j in range(i,m):
            A[r][j]-=fac*A[i][j]
        b[r]-=fac*b[i]
coef=b
errs=[]; by={}
for row,x in zip(rows,features):
    case=row[0]; cost=row[-1]
    pred=sum(c*v for c,v in zip(coef,x))
    err=abs(pred-cost)
    errs.append(err)
    by.setdefault(case,[]).append(err)
print('coef exp fail100 tasks k bias=', [round(c,6) for c in coef], 'mae',round(sum(errs)/len(errs),4),'rmse',round((sum(e*e for e in errs)/len(errs))**0.5,4))
for case in sorted(by):
    print(case,'mae',round(sum(by[case])/len(by[case]),4),'n',len(by[case]))
