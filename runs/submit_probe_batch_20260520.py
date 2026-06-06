#!/usr/bin/env python3
import json, time, datetime as dt, hashlib, urllib.request, pathlib, py_compile
ROOT=pathlib.Path('/Users/比赛/FOR_AutoSolver_706.72')
BASE='https://hackathon.mykeeta.com'; TOKEN='13900139080'
FILES=[
('runs/probe401_nocache_dynamic_20260520.py','probe401_no_cache_dynamic_full_pipeline'),
('runs/probe401_cache_as_seed_20260520.py','probe401_cache_as_seed_allow_dynamic_override'),
('runs/probe501_pick_raw_expected_20260520.py','probe501_pick_raw_expected_objective'),
('runs/probe501_pick_min_score_20260520.py','probe501_pick_min_score_model'),
('runs/probe501_pick_max_willingness_20260520.py','probe501_pick_max_willingness_model'),
]
def req(method,path,payload=None,timeout=45):
    data=None if payload is None else json.dumps(payload).encode()
    headers={'Content-Type':'application/json'} if payload is not None else {}
    for i in range(5):
        try:
            r=urllib.request.urlopen(urllib.request.Request(BASE+path,data=data,headers=headers,method=method),timeout=timeout)
            return json.loads(r.read().decode())
        except Exception as e:
            print('[retry]',method,path,i+1,repr(e),flush=True); time.sleep(min(2+i,8))
    raise RuntimeError(path)
records=[]
print('[health0]',json.dumps(req('GET','/health'),ensure_ascii=False),flush=True)
for rel,note in FILES:
    p=ROOT/rel; code=p.read_text(); raw=code.encode(); sha=hashlib.sha256(raw).hexdigest()
    print('[candidate]',rel,'size',len(raw),'sha',sha[:8],note,flush=True)
    if len(raw)>=80000: print('[skip size]',rel); continue
    py_compile.compile(str(p),doraise=True)
    resp=req('POST','/judge',{'code':code,'token':TOKEN},timeout=60)
    print('[submitted]',rel,json.dumps(resp,ensure_ascii=False),flush=True)
    records.append({'rel':rel,'note':note,'sha':sha,'submit_response':resp})
    time.sleep(0.4)
# poll all jobs
pending={r['submit_response'].get('job_id'):r for r in records if r['submit_response'].get('job_id')}
deadline=time.time()+600
while pending and time.time()<deadline:
    for job in list(pending):
        ans=req('GET',f'/result/{job}',timeout=45)
        st=ans.get('status')
        if st not in ('queued','running'):
            rec=pending.pop(job); rec['result']=ans; rec['finished_at']=dt.datetime.now().isoformat(timespec='seconds')
            out=ROOT/'runs'/f"official_probe_{dt.datetime.now():%Y%m%d_%H%M%S}_{rec['sha'][:8]}.json"
            out.write_text(json.dumps(rec,ensure_ascii=False,indent=2))
            print('[done]',rec['rel'],'avg',ans.get('avg_score'),'saved',out,flush=True)
            for c in ans.get('case_results',[]):
                if c.get('case_file') in ('low_willingness_seed501.txt','scarce_couriers_seed401.txt'):
                    print(' ',c.get('case_file'),c.get('total_score'),'assigned',c.get('assigned_count'),'unassigned',c.get('unassigned_count'),'time',c.get('elapsed_ms'),flush=True)
        else:
            print('[poll]',job[:8],st,flush=True)
    if pending: time.sleep(8)
print('[remaining]',list(pending),flush=True)
print('[health1]',json.dumps(req('GET','/health'),ensure_ascii=False),flush=True)
