#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
END_TS=dt.datetime(2026,5,17,23,50,0)
BASE_SOLVER=ROOT/'solver.py'
RUNS=ROOT/'runs'
LOG=RUNS/f'structural_optimize_until_2350_{dt.datetime.now():%Y%m%d_%H%M%S}.log'
LATEST=RUNS/'structural_optimize_until_2350_latest.log'
BEST_JSON=RUNS/'structural_candidate_leaderboard_latest.json'
KNOWN_OFFICIAL={
 '812ea145dd9a38ebf9abbf16d873c383a299e009ad581821a204cb35780edd34':'baseline official avg 706.7153',
 'c79ee39ae91035caef21de8eeda7685e764ecd6287f5d5c6c130d09f1a59e14e':'bad official avg 712.43',
 '3e0a88d2dfb3a69e4937916c2424280d961c9755bc9852522179fe02dc69b9c1':'bad official avg 712.3718',
}
try:
    if LATEST.exists() or LATEST.is_symlink(): LATEST.unlink()
    LATEST.symlink_to(LOG.name)
except Exception:
    pass

def log(msg):
    line=f'{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}'
    print(line, flush=True)
    with LOG.open('a',encoding='utf-8') as f: f.write(line+'\n')

def sh(cmd,timeout=120,quiet=False):
    try:
        p=subprocess.run(list(map(str,cmd)),cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        if not quiet:
            log('$ '+' '.join(map(str,cmd)))
            out=p.stdout[-4000:]
            print(out,end='' if out.endswith('\n') else '\n',flush=True)
            with LOG.open('a',encoding='utf-8') as f:
                f.write(out)
                if out and not out.endswith('\n'): f.write('\n')
                f.write(f'[exit {p.returncode}]\n')
        return p.returncode,p.stdout
    except Exception as e:
        log(f'[cmd_error] {e!r}')
        return 99,repr(e)

def fp(path):
    b=Path(path).read_bytes(); return len(b),hashlib.sha256(b).hexdigest()

def write_learning(summary,details):
    (ROOT/'.learnings').mkdir(exist_ok=True)
    path=ROOT/'.learnings'/'LEARNINGS.md'
    if not path.exists(): path.write_text('# Learnings\n\n---\n',encoding='utf-8')
    ts=dt.datetime.now().strftime('%Y%m%d-%H%M%S')
    with path.open('a',encoding='utf-8') as f:
        f.write(f"\n## [LRN-{ts}] insight\n\n**Logged**: {dt.datetime.now().isoformat(timespec='seconds')}+08:00\n**Priority**: medium\n**Status**: observed\n**Area**: algorithm\n\n### Summary\n{summary}\n\n### Details\n{details}\n\n### Metadata\n- Source: structural foreground optimizer\n- Related Files: `solver.py`, `runs/structural_optimize_until_2350_latest.log`\n- Tags: autosolver, scarce, stability\n\n---\n")

def eval_variant(path,timeout=420):
    code=r'''
import importlib.machinery, importlib.util, json, sys, time, statistics, random
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
path=Path(sys.argv[1])
loader=importlib.machinery.SourceFileLoader('cand_'+str(abs(hash(str(path)))),str(path))
spec=importlib.util.spec_from_loader(loader.name,loader)
mod=importlib.util.module_from_spec(spec); loader.exec_module(mod)
cases=[('large', (ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt').read_text()),('low025',proxy_eval.make_low(.25)),('scarce40',proxy_eval.make_scarce())]
rows=[]
for name,text in cases:
    parsed,tasks,couriers=proxy_eval.parse(text); T=set(tasks)
    trials={'large':2,'low025':3,'scarce40':6}[name]
    vals=[]; times=[]; groups=[]
    for k in range(trials):
        t0=time.monotonic(); res=mod.solve(text); elapsed=time.monotonic()-t0
        vals.append(mod._solution_expected_cost(res,parsed,T)); times.append(elapsed); groups.append(len(res))
    rows.append({'case':name,'mean':statistics.mean(vals),'median':statistics.median(vals),'best':min(vals),'worst':max(vals),'time_mean':statistics.mean(times),'groups':groups,'vals':vals})
print(json.dumps(rows,ensure_ascii=False))
'''
    rc,out=sh([sys.executable,'-c',code,str(path)],timeout=timeout,quiet=True)
    if rc: return None,out
    try: return json.loads(out.strip().splitlines()[-1]),''
    except Exception as e: return None,out[-1000:]+repr(e)

def rowmap(rows): return {r['case']:r for r in rows}

def score_rows(rows,base=None):
    d=rowmap(rows)
    score=0.0
    if base:
        b=rowmap(base)
        score+=(d['large']['mean']-b['large']['mean'])*3.0
        score+=(d['low025']['mean']-b['low025']['mean'])*0.8
        score+=(d['scarce40']['mean']-b['scarce40']['mean'])*1.0
        score+=(d['scarce40']['worst']-b['scarce40']['worst'])*0.45
    else:
        score+=(d['large']['mean']-657.104)*3.0
        score+=(d['low025']['mean']-1888.63)*0.8
        score+=(d['scarce40']['mean']-1097.85)*1.0
        score+=max(0,d['scarce40']['worst']-1097.85)*0.45
    score+=max(0,d['large']['time_mean']-8.2)*20.0
    score+=max(0,d['scarce40']['time_mean']-9.2)*10.0
    if min(d['scarce40']['groups'])<39: score+=80.0
    return score

def repl_once(s,old,new,name):
    if old not in s:
        log(f'[mutate_warn] missing pattern for {name}: {old[:80]}')
        return s
    return s.replace(old,new,1)

def apply_edit(s, edit):
    kind=edit[0]
    if kind=='cols':
        _,cols,beam=edit
        return s.replace('max_columns=1150',f'max_columns={cols}',1).replace('beam_width=5200',f'beam_width={beam}',1)
    if kind=='seed':
        _,seedn=edit
        return s.replace('for(c,(T,D))in enumerate(J[:8]):',f'for(c,(T,D))in enumerate(J[:{seedn}]):',1)
    if kind=='top':
        _,one,multi,maxcombo=edit
        old='H=len(A[0][1]);f=8 if H==1 else 9;A=A[:f];g=2 if H==1 else min(3,len(A));M=[]'
        new=f'H=len(A[0][1]);f={one} if H==1 else {multi};A=A[:f];g=2 if H==1 else min({maxcombo},len(A));M=[]'
        return repl_once(s,old,new,f'top{one}_{multi}_{maxcombo}')
    if kind=='order':
        _,name=edit
        old='def _scarce_column_order_key(column):A,B,C,D,E,F=column;G=_popcount(C);H=_popcount(D);return F,A/max(1,H),G,A/max(B,1e-09),A,-len(E)'
        forms={
            'cover':'def _scarce_column_order_key(column):A,B,C,D,E,F=column;G=_popcount(C);H=_popcount(D);return G,A/max(1,H),F,A/max(B,1e-09),A,-len(E)',
            'density':'def _scarce_column_order_key(column):A,B,C,D,E,F=column;G=_popcount(C);H=_popcount(D);return A/max(1,H),G,F,A/max(B,1e-09),A,-len(E)',
            'saving':'def _scarce_column_order_key(column):A,B,C,D,E,F=column;G=_popcount(C);H=_popcount(D);return A,A/max(1,H),G,F,A/max(B,1e-09),-len(E)',
        }
        return repl_once(s,old,forms[name],f'order_{name}')
    if kind=='polish_less':
        return s.replace("if time.monotonic()<D-.85:A=_column_alns_repair_solution(A,B,C,min(D,time.monotonic()+.75),mode=_J,max_window_tasks=12,top_riders_per_task_key=8,option_limit=55,max_k=4);A=_drop_unprofitable_groups(A,B,C)","if time.monotonic()<D-.65:A=_column_alns_repair_solution(A,B,C,min(D,time.monotonic()+.52),mode=_J,max_window_tasks=10,top_riders_per_task_key=7,option_limit=45,max_k=3);A=_drop_unprofitable_groups(A,B,C)",1)
    if kind=='polish_bundle':
        return s.replace('max_windows=34,max_window_tasks=14','max_windows=48,max_window_tasks=14',1)
    return s

def mutate(base_text,round_no):
    s=base_text; out=[]
    def add(name,text):
        if text!=s: out.append((name,text))
    # Scarce elite recombine width/depth. These are structural, not previous low/sparse micro-knobs.
    for cols,beam in [(850,3600),(1000,4400),(1300,5600),(1500,6200),(1800,7200)]:
        t=s.replace('max_columns=1150',f'max_columns={cols}',1).replace('beam_width=5200',f'beam_width={beam}',1)
        add(f'scarce_cols{cols}_beam{beam}',t)
    for seedn in [4,6,10,12,16]:
        t=s.replace('for(c,(T,D))in enumerate(J[:8]):',f'for(c,(T,D))in enumerate(J[:{seedn}]):',1)
        add(f'scarce_seedtop{seedn}',t)
    for one,multi,maxcombo in [(6,7,2),(7,8,2),(8,7,2),(10,10,3),(12,12,3)]:
        old='H=len(A[0][1]);f=8 if H==1 else 9;A=A[:f];g=2 if H==1 else min(3,len(A));M=[]'
        new=f'H=len(A[0][1]);f={one} if H==1 else {multi};A=A[:f];g=2 if H==1 else min({maxcombo},len(A));M=[]'
        add(f'scarce_top{one}_{multi}_k{maxcombo}',repl_once(s,old,new,f'top{one}_{multi}_{maxcombo}'))
    # Change prune ordering to prefer coverage/task density before source rank; may stabilize 39/40 scarce.
    old='def _scarce_column_order_key(column):A,B,C,D,E,F=column;G=_popcount(C);H=_popcount(D);return F,A/max(1,H),G,A/max(B,1e-09),A,-len(E)'
    forms=[
        ('scarce_order_cover_first','def _scarce_column_order_key(column):A,B,C,D,E,F=column;G=_popcount(C);H=_popcount(D);return G,A/max(1,H),F,A/max(B,1e-09),A,-len(E)'),
        ('scarce_order_density_first','def _scarce_column_order_key(column):A,B,C,D,E,F=column;G=_popcount(C);H=_popcount(D);return A/max(1,H),G,F,A/max(B,1e-09),A,-len(E)'),
        ('scarce_order_saving_first','def _scarce_column_order_key(column):A,B,C,D,E,F=column;G=_popcount(C);H=_popcount(D);return A,A/max(1,H),G,F,A/max(B,1e-09),-len(E)'),
    ]
    for name,new in forms: add(name,repl_once(s,old,new,name))
    # Conservative final polish variants only inside scarce branch.
    add('scarce_polish_less_alns',s.replace("if time.monotonic()<D-.85:A=_column_alns_repair_solution(A,B,C,min(D,time.monotonic()+.75),mode=_J,max_window_tasks=12,top_riders_per_task_key=8,option_limit=55,max_k=4);A=_drop_unprofitable_groups(A,B,C)","if time.monotonic()<D-.65:A=_column_alns_repair_solution(A,B,C,min(D,time.monotonic()+.52),mode=_J,max_window_tasks=10,top_riders_per_task_key=7,option_limit=45,max_k=3);A=_drop_unprofitable_groups(A,B,C)",1))
    add('scarce_polish_more_bundle',s.replace('max_windows=34,max_window_tasks=14','max_windows=48,max_window_tasks=14',1))
    # Later rounds test pair/triple combinations among the least-bad structural families.
    combo_sets=[
        [('cols',1000,4400),('cols',1800,7200),('order','density'),('top',7,8,2),('seed',4),('polish_less',)],
        [('cols',850,3600),('cols',1300,5600),('order','density'),('top',8,7,2),('seed',6),('polish_bundle',)],
        [('cols',900,3800),('cols',1050,4600),('cols',1200,5000),('order','cover'),('top',7,8,2),('seed',5),('seed',7)],
    ]
    edits=combo_sets[min(max(round_no-2,0),len(combo_sets)-1)]
    if round_no>=2:
        import itertools as _it
        max_len=2 if round_no<4 else 3
        for r in range(2,max_len+1):
            for combo in _it.combinations(edits,r):
                text=s; names=[]
                for edit in combo:
                    text=apply_edit(text,edit); names.append('_'.join(map(str,edit)))
                add('combo_'+'__'.join(names),text)
    return out

log(f'[start_structural] target_end={END_TS}')
size,sha=fp(BASE_SOLVER); log(f'[baseline] size={size} sha={sha} cache={KNOWN_OFFICIAL.get(sha,"new/unknown")}')
sh([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py'],timeout=60)
sh([sys.executable,'_bench.py','solver.py','1'],timeout=50)
base_rows,err=eval_variant(BASE_SOLVER)
if not base_rows:
    log('[fatal] baseline proxy failed '+err[:500]); sys.exit(2)
log('[baseline_proxy_robust] '+json.dumps(base_rows,ensure_ascii=False))
base_text=BASE_SOLVER.read_text(encoding='utf-8')
leader=[]; seen=set(); round_no=0; last_learning=dt.datetime.now()
while dt.datetime.now()<END_TS:
    round_no+=1
    log(f'[round {round_no}] remaining_min={(END_TS-dt.datetime.now()).total_seconds()/60:.1f}')
    candidates=mutate(base_text,round_no)
    random.Random(1000+round_no).shuffle(candidates)
    evaluated_this_round=0
    for name,text in candidates:
        if dt.datetime.now()>=END_TS: break
        path=RUNS/f'struct_{round_no}_{name}.py'
        path.write_text(text,encoding='utf-8')
        size,sha=fp(path)
        if sha in seen:
            continue
        seen.add(sha)
        evaluated_this_round+=1
        rc,_=sh([sys.executable,'-m','py_compile',str(path)],timeout=20,quiet=True)
        if rc:
            log(f'[candidate_bad_compile] {name} sha={sha[:8]}')
            continue
        rows,err=eval_variant(path)
        if not rows:
            log(f'[candidate_error] {name} sha={sha[:8]} {err[:300]}')
            continue
        local_score=score_rows(rows,base_rows)
        item={'score':local_score,'name':name,'path':str(path),'size':size,'sha':sha,'rows':rows,'time':dt.datetime.now().isoformat(timespec='seconds')}
        leader.append(item); leader=sorted(leader,key=lambda x:x['score'])[:25]
        BEST_JSON.write_text(json.dumps(leader,ensure_ascii=False,indent=2),encoding='utf-8')
        cache=KNOWN_OFFICIAL.get(sha,'new')
        log(f'[candidate] {name} local_delta_score={local_score:.3f} sha={sha[:8]} cache={cache} rows='+json.dumps(rows,ensure_ascii=False))
        d=rowmap(rows); b=rowmap(base_rows)
        robust = local_score < -12 and d['large']['mean'] <= b['large']['mean']+1 and d['low025']['mean'] <= b['low025']['mean']+8 and d['scarce40']['worst'] <= b['scarce40']['worst']-10 and min(d['scarce40']['groups'])>=39
        if robust:
            best_path=RUNS/f'HIGH_CONF_STRUCT_{name}_{sha[:8]}.py'
            shutil.copy(path,best_path)
            log(f'[high_conf_local_saved] {best_path} local_delta_score={local_score:.3f}; NOT submitted automatically; run safe submit after review/cache check')
            write_learning(f'High-confidence structural scarce candidate saved: {name}',f'Path `{best_path}`, sha `{sha}`, delta `{local_score:.3f}`, rows `{json.dumps(rows,ensure_ascii=False)}`. Official submission still requires manual review and safe script.')
    log('[leader_top] '+json.dumps(leader[:5],ensure_ascii=False))
    if evaluated_this_round==0:
        log('[idle] no new candidates this round; sleeping 60s to avoid log spam')
        time.sleep(60)
    if (dt.datetime.now()-last_learning).total_seconds()>3600:
        write_learning('Structural optimizer hourly checkpoint',f'No automatic official submit. Current top candidates: `{json.dumps(leader[:3],ensure_ascii=False)}`')
        last_learning=dt.datetime.now()
log('[done] target reached 23:50')
