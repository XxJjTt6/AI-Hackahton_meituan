#!/usr/bin/env python3
import itertools, json, re, shutil, subprocess, time, sys
from pathlib import Path
sys.path.insert(0, '/Users/比赛/FOR_AutoSolver_706.72')
import runs.proxy_eval as pe
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
BASE=ROOT/'runs/kdd_seedpair_early_fastpolish.py'
OUT=ROOT/'runs/seedpair_param_scan'
OUT.mkdir(exist_ok=True)
base_text=BASE.read_text()
params=[]
for budget in [0.30,0.34,0.38,0.42]:
  for top_items in [24,28,32]:
    for seed_limit in [48,64,84]:
      for late_budget, windows in [(0.0,0),(1.2,28),(1.6,34)]:
        params.append((budget,top_items,seed_limit,late_budget,windows))

def make_variant(idx,p):
    budget,top_items,seed_limit,late_budget,windows=p
    s=base_text
    s=re.sub(r'time\.monotonic\(\)\+\.42', f'time.monotonic()+{budget}', s, count=1)
    s=re.sub(r'items=items\[:32\]', f'items=items[:{top_items}]', s)
    s=re.sub(r'len\(seeds\)>=84', f'len(seeds)>={seed_limit}', s)
    if late_budget==0:
        s=re.sub(r"\tif f and time\.monotonic\(\)<A-2\.25:\n\t\tQ=_scarce_bundle_insertion_repair_solution\(D,C,B,min\(A,time\.monotonic\(\)\+1\.95\),max_windows=42,max_window_tasks=14\)\n\t\tif _solution_expected_cost\(Q,C,B\)<_solution_expected_cost\(D,C,B\)-1e-09:\n\t\t\tD=_drop_unprofitable_groups\(Q,C,B\)\n\t\t\tif time\.monotonic\(\)<A-\.2:\n\t\t\t\tK=_reassign_mixed_solution\(D,C,B,min\(A,time\.monotonic\(\)\+\.18\)\)\n\t\t\t\tif _solution_expected_cost\(K,C,B\)<_solution_expected_cost\(D,C,B\)-1e-09:D=K\n",
                 "\tif f and time.monotonic()<A-.95:\n\t\tK=_reassign_mixed_solution(D,C,B,min(A,time.monotonic()+.2))\n\t\tif _solution_expected_cost(K,C,B)<_solution_expected_cost(D,C,B)-1e-09:D=K\n", s)
    else:
        s=s.replace('time.monotonic()+1.95', f'time.monotonic()+{late_budget}')
        s=s.replace('max_windows=42', f'max_windows={windows}')
    path=OUT/f'cand_{idx:03d}_b{budget}_top{top_items}_lim{seed_limit}_late{late_budget}_w{windows}.py'
    path.write_text(s)
    return path

def eval_variant(path):
    mod=pe.load(path)
    cases=[('large',pe.DATA.read_text(),1),('low025',pe.make_low(.25),1),('scarce40',pe.make_scarce(),3)]
    score=0; detail={}
    for name,text,reps in cases:
        rows,tasks,couriers=pe.parse(text); tasks=set(tasks); vals=[]; times=[]; structs=[]
        for _ in range(reps):
            t0=time.monotonic(); res=mod.solve(text); dt=time.monotonic()-t0
            cost=mod._solution_expected_cost(res,rows,tasks); kd={}
            for k,cs in res: kd[len(cs)]=kd.get(len(cs),0)+1
            vals.append(cost); times.append(dt); structs.append(kd)
        detail[name]={'mean':sum(vals)/len(vals),'best':min(vals),'worst':max(vals),'tmax':max(times),'structs':structs}
    score=(detail['large']['mean']-657.10)*5 + (detail['low025']['mean']-1891.05)*0.2 + (detail['scarce40']['mean']-1097.85)*0.9
    score += max(0,detail['large']['tmax']-8.9)*25 + max(0,detail['low025']['tmax']-9.2)*20 + max(0,detail['scarce40']['tmax']-9.6)*35
    return score,detail

leader=[]
for idx,p in enumerate(params[:60]):
    path=make_variant(idx,p)
    try:
        subprocess.check_call(['python3','-m','py_compile',str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        score,detail=eval_variant(path)
    except Exception as e:
        print('ERR',idx,p,e,flush=True); continue
    rec={'idx':idx,'params':p,'path':str(path),'score':score,'detail':detail}
    leader.append(rec); leader.sort(key=lambda r:r['score']); leader=leader[:10]
    print(f"[{idx:03d}] score={score:.2f} p={p} scarce_mean={detail['scarce40']['mean']:.2f} scarce_tmax={detail['scarce40']['tmax']:.2f} low={detail['low025']['mean']:.2f} large_t={detail['large']['tmax']:.2f}", flush=True)
    print('  best:', [(r['idx'], round(r['score'],2), r['params'], round(r['detail']['scarce40']['mean'],2), round(r['detail']['scarce40']['tmax'],2)) for r in leader[:3]], flush=True)
    (ROOT/'runs/seedpair_param_scan_latest.json').write_text(json.dumps(leader,indent=2))
print('DONE')
