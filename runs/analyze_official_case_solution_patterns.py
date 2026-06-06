import glob,json,collections,os
by=collections.defaultdict(list)
for p in glob.glob('runs/official_submit_*.json'):
    try:d=json.load(open(p)); res=d['result']; sha=d.get('sha256','')[:8]
    except Exception: continue
    avg=res.get('avg_score')
    for c in res.get('case_results',[]):
        if c.get('status')!='ok' or not c.get('validity'): continue
        groups=[]
        for g in c.get('detail',[]):
            groups.append((g.get('task_id_list'), tuple(g.get('couriers',[])), float(g.get('cost',0)), float(g.get('p_complete',0)), float(g.get('expected_score',0))))
        sig=tuple(sorted((k,cs) for k,cs,_,_,_ in groups))
        by[c['case_file']].append(dict(score=c['total_score'],assigned=c.get('assigned_count'),unassigned=c.get('unassigned_count'),elapsed=c.get('elapsed_ms'),sha=sha,avg=avg,file=os.path.basename(p),sig=sig,groups=groups))
for case, rows in sorted(by.items()):
    rows.sort(key=lambda r:(r['score'], r['elapsed']))
    cur=[r for r in rows if r['sha']=='f65d16ac']
    cur_score=cur[0]['score'] if cur else None
    print('\nCASE',case,'current',cur_score,'unique_sigs',len({r['sig'] for r in rows}))
    seen=set(); shown=0
    for r in rows:
        if r['sig'] in seen: continue
        seen.add(r['sig']); shown+=1
        mark='CUR' if r['sha']=='f65d16ac' else ''
        print(f"  {shown:2d} score={r['score']:9.4f} assigned={r['assigned']:2} un={r['unassigned']} ms={r['elapsed']:5} sha={r['sha']} avg={r['avg']} {mark} {r['file']}")
        if shown>=6: break
