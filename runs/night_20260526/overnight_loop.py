#!/usr/bin/env python3
import datetime as dt, hashlib, json, os, random, re, subprocess, sys, time, urllib.request, urllib.error
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
BASE='https://hackathon.mykeeta.com'; TOKEN='13900139080'
SRC=ROOT/'solver.py'; OUTDIR=ROOT/'runs/night_20260526'; OUTDIR.mkdir(parents=True,exist_ok=True)
LOG=OUTDIR/'overnight_loop.log'; STATE=OUTDIR/'overnight_state.json'
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
END_TS=dt.datetime(2026,5,27,9,0).timestamp()
MAX_SUBMITS=12
# Strong gate: require meaningful official-like movement and guard preservation.
OFFICIAL_LIKE_GATE=1600.0
BASELINE_LIKE=1616.75860162171
BASELINE_CALIB=1199.1284207596611
BASELINE_LARGE=657.1040208060375

def log(msg):
    line=f"[{dt.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line,flush=True)
    with LOG.open('a') as f: f.write(line+'\n')

def load_state():
    if STATE.exists():
        try: return json.loads(STATE.read_text())
        except Exception: pass
    return {'iters':0,'submits':0,'seen':{},'best':[]}

def save_state(s): STATE.write_text(json.dumps(s,indent=2,sort_keys=True))

CHILD=r'''
import importlib.util,json,sys,time,hashlib
from pathlib import Path
root=Path('/Users/比赛/FOR_AutoSolver_706.72'); path=Path(sys.argv[1]); case=sys.argv[2]
sys.path.insert(0,str(root/'runs'))
import proxy_eval
texts={'official_like':(root/'runs/official_like_low_synth.txt').read_text(),'calibrated':(root/'runs/official_calibrated_low_synth.txt').read_text(),'low025':proxy_eval.make_low(.25),'low030':proxy_eval.make_low(.30),'large':proxy_eval.DATA.read_text(),'scarce40':proxy_eval.make_scarce()}
text=texts[case]; rows,tasks,c=proxy_eval.parse(text); T=set(tasks)
spec=importlib.util.spec_from_file_location('cand',str(path)); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
t=time.monotonic(); out=m.solve(text); dt=time.monotonic()-t
cost=m._solution_expected_cost(out,rows,T); cov=m._solution_covered_count(out,rows)
shape={}
for k,cs in out: shape[str(len(cs))]=shape.get(str(len(cs)),0)+1
print(json.dumps({'case':case,'cost':cost,'time':dt,'cov':cov,'sig':hashlib.sha1(repr(sorted((k,tuple(cs)) for k,cs in out)).encode()).hexdigest()[:12],'shape':shape,'rows':len(out)}))
'''

EDITS=[
 ('bias_on', 'if _D and J and not _LOW_BIAS_ACTIVE:', 'if _B and J and not _LOW_BIAS_ACTIVE:'),
 ('scale_020', 'AC=(.25,_E/3.,.5)if J else(_E/3.,)', 'AC=(.2,_E/3.,.5)if J else(_E/3.,)'),
 ('scale_040', 'AC=(.25,_E/3.,.5)if J else(_E/3.,)', 'AC=(.25,.4,.55)if J else(_E/3.,)'),
 ('global_wide', 'top_riders_per_task_key=8,max_k=4,option_limit=28)', 'top_riders_per_task_key=10,max_k=5,option_limit=38)'),
 ('low_wide', 'top_riders_per_task_key=10,max_k=3,option_limit=28)', 'top_riders_per_task_key=13,max_k=4,option_limit=44)'),
 ('worst_16', 'for(N,O)in((8,range(0,8)),(10,range(0,8)),(12,range(0,8))):', 'for(N,O)in((8,range(0,8)),(12,range(0,8)),(16,range(0,6))):'),
 ('deep_16', 'for N in(8,10,12):\n\t\tfor O in range(10):', 'for N in(8,12,16):\n\t\tfor O in range(8):'),
 ('late_16', 'F=(8,10,12,14)[B%4]', 'F=(8,10,12,14,16)[B%5]'),
 ('rank_score', 'B=sorted(B,key=lambda c:(_group_expected_cost([c],len(c[1])),-c[4],c[5]))[:top_riders_per_task_key]', 'B=sorted(B,key=lambda c:(c[3],-c[4],c[5]))[:top_riders_per_task_key]'),
 ('rank_willing', 'B=sorted(B,key=lambda c:(_group_expected_cost([c],len(c[1])),-c[4],c[5]))[:top_riders_per_task_key]', 'B=sorted(B,key=lambda c:(-c[4],c[3],c[5]))[:top_riders_per_task_key]'),
 ('reserve_deep', 'if J and time.monotonic()<A-1.35:D=_low_deep_window_repair_solution(D,C,B,min(A,time.monotonic()+1.2))', 'if J and time.monotonic()<A-1.65:D=_low_deep_window_repair_solution(D,C,B,min(A,time.monotonic()+1.5))'),
 ('reserve_late', 'if J and time.monotonic()<A-.95:D=_low_late_acceptance_repair_solution(D,C,B,min(A,time.monotonic()+.85))', 'if J and time.monotonic()<A-1.25:D=_low_late_acceptance_repair_solution(D,C,B,min(A,time.monotonic()+1.15))'),

 ('pick_slack_10', 'if H<=C+25.:return F', 'if H<=C+10.:return F'),
 ('pick_slack_60', 'if H<=C+25.:return F', 'if H<=C+60.:return F'),
 ('pick_min_weight', 'H=.45*D+.45*F+.1*G', 'H=.25*D+.65*F+.1*G'),
 ('pick_maxw_weight', 'H=.45*D+.45*F+.1*G', 'H=.3*D+.35*F+.35*G'),
 ('pick_less_guard', 'return H+.15*max(_C,I),max(D,F,G),D', 'return H+.05*max(_C,I),max(D,F,G),D'),
 ('pick_more_guard', 'return H+.15*max(_C,I),max(D,F,G),D', 'return H+.3*max(_C,I),max(D,F,G),D'),

 ('group_cost_min_order', 'for(M,F)in enumerate(A):\n\t\t\t\tif L>>M&1:D*=F[4];K+=F[3];E+=1\n\t\t\t\telse:D*=_E-F[4]', 'for(M,F)in enumerate(sorted(A,key=lambda c:(c[3],-c[4],c[5]))):\n\t\t\t\tif L>>M&1:D*=F[4];K+=F[3];E+=1\n\t\t\t\telse:D*=_E-F[4]'),
 ('group_cost_will_order', 'for(M,F)in enumerate(A):\n\t\t\t\tif L>>M&1:D*=F[4];K+=F[3];E+=1\n\t\t\t\telse:D*=_E-F[4]', 'for(M,F)in enumerate(sorted(A,key=lambda c:(-c[4],c[3],c[5]))):\n\t\t\t\tif L>>M&1:D*=F[4];K+=F[3];E+=1\n\t\t\t\telse:D*=_E-F[4]'),
 ('low_global_top12', 'return _search_column_window(A,all_tasks,deadline,top_riders_per_task_key=8,max_k=4,option_limit=28)', 'return _search_column_window(A,all_tasks,deadline,top_riders_per_task_key=12,max_k=5,option_limit=50)'),
 ('low_global_top16_k3', 'return _search_column_window(A,all_tasks,deadline,top_riders_per_task_key=8,max_k=4,option_limit=28)', 'return _search_column_window(A,all_tasks,deadline,top_riders_per_task_key=16,max_k=3,option_limit=80)'),
]

def make_candidate(rng, idx):
    src=SRC.read_text(); names=[]
    # choose compatible edits; duplicate targets are skipped if already replaced
    for name,old,new in rng.sample(EDITS, rng.randint(1,4)):
        if old in src and rng.random()<0.9:
            src=src.replace(old,new,1); names.append(name)
    if not names: return None,None,None
    path=OUTDIR / (f'auto_cand_{idx:05d}_' + '-'.join(names) + '.py')
    path.write_text(src)
    return path,names,hashlib.sha256(src.encode()).hexdigest()

def run_case(path, case, timeout=45):
    cp=subprocess.run([sys.executable,'-c',CHILD,str(path),case],text=True,capture_output=True,timeout=timeout)
    if cp.returncode: return {'err':(cp.stderr or cp.stdout)[-1000:]}
    return json.loads(cp.stdout)

def eval_candidate(path):
    res={}
    for case,n in [('official_like',2),('calibrated',1),('low025',1),('low030',1),('large',1),('scarce40',1)]:
        rows=[]
        for _ in range(n): rows.append(run_case(path,case))
        res[case]=rows
    return res

def mean_cost(rows):
    vals=[r['cost'] for r in rows if 'cost' in r and r['cost']!=float('inf')]
    return sum(vals)/len(vals) if vals else float('inf')

def passes(res):
    like=mean_cost(res['official_like']); calib=mean_cost(res['calibrated']); large=mean_cost(res['large']); scarce=mean_cost(res['scarce40'])
    return like<=OFFICIAL_LIKE_GATE and calib<=BASELINE_CALIB+1e-6 and large<=BASELINE_LARGE+1.0 and scarce<=1110

def request_json(method,path,payload=None,timeout=30):
    data=None if payload is None else json.dumps(payload).encode()
    headers={'Content-Type':'application/json'} if payload is not None else {}
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=timeout) as resp: return json.loads(resp.read().decode())

def submit(path, sha, note):
    code=path.read_text(); raw=code.encode()
    if len(raw)>=80000: raise RuntimeError('too large')
    subprocess.run([sys.executable,'-m','py_compile',str(path)],cwd=ROOT,check=True,timeout=30)
    subprocess.run([sys.executable,'-m','unittest','tests.test_main'],cwd=ROOT,check=True,timeout=30)
    subprocess.run([sys.executable,'_bench.py',str(path),'1'],cwd=ROOT,check=True,timeout=45)
    health=request_json('GET','/health',timeout=15)
    rec={'started_at':dt.datetime.now().isoformat(timespec='seconds'),'solver':str(path),'sha256':sha,'note':note,'health':health}
    resp=request_json('POST','/judge',{'code':code,'token':TOKEN},timeout=60); rec['submit_response']=resp
    job=resp.get('job_id')
    deadline=time.time()+420; result=None
    while job and time.time()<deadline:
        time.sleep(3); r=request_json('GET',f'/result/{job}',timeout=30)
        if r.get('status') not in ('queued','running'):
            result=r; break
    rec['finished_at']=dt.datetime.now().isoformat(timespec='seconds'); rec['result']=result or {'status':'timeout'}
    out=ROOT/'runs'/f'official_submit_{dt.datetime.now():%Y%m%d_%H%M%S}_{sha[:8]}.json'
    out.write_text(json.dumps(rec,indent=2,ensure_ascii=False)); return rec,out

def main():
    st=load_state(); rng=random.Random(202605260900+st['iters'])
    log(f'start overnight loop until 2026-05-27 09:00, existing submits={st["submits"]}')
    while time.time()<END_TS and st['submits']<MAX_SUBMITS:
        idx=st['iters']; st['iters']+=1
        cand=make_candidate(rng, idx)
        if cand[0] is None: continue
        path,names,sha=cand
        if sha in st['seen']: continue
        st['seen'][sha]=names
        try: res=eval_candidate(path)
        except Exception as e:
            log(f'iter {idx} {names} eval_error {e!r}'); save_state(st); continue
        like=mean_cost(res['official_like']); calib=mean_cost(res['calibrated']); low25=mean_cost(res['low025']); low30=mean_cost(res['low030']); large=mean_cost(res['large']); scarce=mean_cost(res['scarce40'])
        entry={'iter':idx,'sha':sha,'path':str(path),'names':names,'like':like,'calib':calib,'low025':low25,'low030':low30,'large':large,'scarce40':scarce,'res':res}
        st['best'].append(entry); st['best']=sorted(st['best'],key=lambda x:x['like'])[:50]
        log(f'iter {idx} {sha[:8]} {names} like={like:.3f} calib={calib:.3f} low025={low25:.3f} low030={low30:.3f} large={large:.3f} scarce={scarce:.3f}')
        if passes(res):
            log(f'candidate {sha[:8]} passes strong gate, submitting; names={names}')
            try:
                rec,out=submit(path,sha,'overnight-auto-strong-low-gate-'+sha[:8])
                st['submits']+=1; entry['official_result']=str(out); log(f'submitted {sha[:8]} saved={out} result={rec.get("result",{}).get("avg_score")}')
            except Exception as e:
                log(f'submit_error {sha[:8]} {e!r}')
        save_state(st)
    log(f'finished loop iters={st["iters"]} submits={st["submits"]}')
if __name__=='__main__': main()
