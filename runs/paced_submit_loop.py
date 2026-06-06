#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
RUNS=ROOT/'runs'
END=dt.datetime(2026,5,17,23,50,0)
LOG=RUNS/f'paced_submit_loop_{dt.datetime.now():%Y%m%d_%H%M%S}.log'
LATEST=RUNS/'paced_submit_loop_latest.log'
try:
    if LATEST.exists() or LATEST.is_symlink(): LATEST.unlink()
    LATEST.symlink_to(LOG.name)
except Exception:
    pass
TARGET_REMAINING=2
SUBMIT_SPACING_MIN=25

KNOWN_OFFICIAL={
 '812ea145dd9a38ebf9abbf16d873c383a299e009ad581821a204cb35780edd34':'baseline 706.7153',
 '6395cbc62e94d9f3d46508f93137f2056da5c05059a75936811070da83cab14f':'baseline_equal submit1',
 'c0a0a8406e355c1dd4669764f6c614aa1519ae8fda689734e3c43b724059ee08':'bad 714.4215 submit2',
 'd8a471261b2961cdd16f2b0d79d10ba87b54caddbf92dab73f940c34a1c33743':'baseline_equal submit3',
 '23299900e98ad6128fdbe6256933863d475890b180d0dbb7f5fa164c5cffb8f8':'bad 712.4961 submit4',
 '0d615014a7f3a7c1cae03d0efbbd1276f3e2116926a7ea804355a24f1d92326e':'bad 712.4379 submit5',
 '6459ac54279120d360bcacbaab6ad52d95e6cf3be4362e53858f7e53f02afbdd':'baseline_equal submit6',
 'c79ee39ae91035caef21de8eeda7685e764ecd6287f5d5c6c130d09f1a59e14e':'bad 712.43 old',
 '3e0a88d2dfb3a69e4937916c2424280d961c9755bc9852522179fe02dc69b9c1':'bad 712.3718 old',
 '74a88fd1ab13b0c33a387c65642dce53ca5bf67cb5af7f7992aa1e483e1c5e1c':'baseline_equal 19:00',
 '61f442090a46186ae26151400fb9639567a749c65de6abf738190b0a0812f1db':'bad 712.4379 19:30 timing shrink scarce regression',
 'f97141e4fc5e1ed7b7b874f98e7e7b4c422ed0370d1011060783d4f18ec5073f':'baseline_equal 20:00 shadow penalty80 no-op',
 '38f7e9a7747e9b59621598be9ff7ef8a021c3c37131489af22cde30c11c74d8f':'baseline_equal 20:30 hard_scarce_drop3 no-op',
 '2696b79ce06daced3f1f2696cc79834565fa429c4939ffa6523d8a67b4c6c1d4':'skip hard_scarce_top6 low signal after drop3 no-op',
 '7ecc56c6584d2a477a1dc92daf995054c53eeacb62a716ebe332cfa9e239c63b':'skip normal_time_guard likely no-op/noisy',
 'b3e2d9358ec00e6187df7774175b0edfdfd062d96b218e0a223ddc31a0baa44e':'skip fg_reassign_long weak/noisy',
 'fe835873b0215c92e8ec7b419b4b2ce89516dfa3fc259308f4025bbaaa1c0731':'skip shadow100 too close to no-op shadow80 unless final desperation',
 '0c7f1a00b918397759f519fc170e806264f07fd326b98a7b99e70ad58c67aba9':'skip pair_rewire_pool5_fast same family after pool9 regression unless final desperation',
 'bf5a4b2b7e8ace32bea75353657e858d450c5dd767f22cdee964c90705fda4ad':'bad 712.4379 pair_rewire_pool9 scarce regression',
 '1aa1774ea9690677d06b9c7a0b68d619dae599ec8477059f9aafb79dd154b85f':'bad 712.4379 hgs_srexlite_repolish scarce regression',
}

def log(msg):
    line=f'{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}'
    print(line, flush=True)
    with LOG.open('a',encoding='utf-8') as f: f.write(line+'\n')

def sha_path(path):
    b=Path(path).read_bytes(); return hashlib.sha256(b).hexdigest(),len(b)

def sh(cmd,timeout=600):
    log('$ '+' '.join(map(str,cmd)))
    p=subprocess.run(list(map(str,cmd)),cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    out=p.stdout
    print(out[-12000:], flush=True)
    with LOG.open('a',encoding='utf-8') as f: f.write(out+'\n[exit %s]\n'%p.returncode)
    return p.returncode,out

def official_shas_from_files():
    out=dict(KNOWN_OFFICIAL)
    for p in RUNS.glob('official_submit_*.json'):
        try:
            j=json.loads(p.read_text())
            sha=j.get('sha256')
            res=j.get('result') or {}
            if sha: out[sha]=f"file {p.name} avg={res.get('avg_score')}"
        except Exception:
            pass
    return out

def next_slots(n):
    now=dt.datetime.now()
    # Half-hour cadence: :00 and :30, starting at the next boundary at least 8 min away.
    slots=[]; cur=now.replace(second=0,microsecond=0)
    minute=30 if cur.minute<30 else 60
    cur=cur.replace(minute=0)+dt.timedelta(minutes=minute)
    if (cur-now).total_seconds()<8*60: cur+=dt.timedelta(minutes=30)
    if n==4 and now < dt.datetime(2026,5,17,21,0,0):
        return [dt.datetime(2026,5,17,h,m,0) for h,m in [(21,0),(22,0),(23,0),(23,30)]]
    if n==3 and now < dt.datetime(2026,5,17,22,0,0):
        return [dt.datetime(2026,5,17,h,m,0) for h,m in [(22,0),(23,0),(23,30)]]
    if n==2 and now < dt.datetime(2026,5,17,23,0,0):
        return [dt.datetime(2026,5,17,h,m,0) for h,m in [(23,0),(23,30)]]
    while cur<END and len(slots)<n:
        slots.append(cur); cur+=dt.timedelta(minutes=30)
    # If too few slots, add tighter final slots after 21:00 but still spaced.
    cur=dt.datetime(2026,5,17,21,0,0)
    while len(slots)<n and cur<END:
        if cur>now and cur not in slots: slots.append(cur)
        cur+=dt.timedelta(minutes=25)
    return sorted(slots)[:n]

def write_learning(summary,details):
    with (ROOT/'.learnings'/'LEARNINGS.md').open('a',encoding='utf-8') as f:
        f.write(f"\n## [LRN-{dt.datetime.now():%Y%m%d-%H%M%S}] paced_submission\n\n**Logged**: {dt.datetime.now().isoformat(timespec='seconds')}+08:00\n**Priority**: medium\n**Status**: observed\n**Area**: official_submission\n\n### Summary\n{summary}\n\n### Details\n{details}\n\n### Metadata\n- Source: paced submit loop\n- Related Files: `runs/paced_submit_loop_latest.log`\n- Tags: autosolver, submission_budget\n\n---\n")

BASE=(ROOT/'solver.py').read_text()

def make_candidate(round_no):
    # Deterministic rotating mutations. Most are small, baseline-near probes.
    variants=[]
    def add(name,text):
        variants.append((name,text))
    s=BASE
    for ext in ['hgs_normal_granular_more.py','hgs_coverage_first_picker.py','hgs_srexlite_repolish.py']:
        ep=RUNS/ext
        if ep.exists(): add(ext[:-3], ep.read_text())
    # Timing-only microtunes were officially harmful; do not generate them.
    # Preserve confirmed pair rewires but test normal/small time reallocations.
    add('normal_time_guard', s.replace('if 9<=L<=35 and not G and not F and time.monotonic()<A-.85:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.45))\n\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.95:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.75))','if 9<=L<=35 and not G and not F and time.monotonic()<A-.65:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.35))\n\tif 9<=L<=35 and not G and not F and time.monotonic()<A-.75:D=_normal_worst_related_repair_solution(D,C,B,min(A,time.monotonic()+.55))',1))
    # Lighter or heavier scarce post-processing around confirmed pair-rewire.
    # Do not generate scarce_skip_eject_shift; officially regressed scarce coverage.
    add('scarce_pair_pool7', s.replace('D=_best_group_from_pool(S,2,min(len(I)+1,6))','D=_best_group_from_pool(S,2,min(len(I)+1,7))',1).replace('E=_best_group_from_pool(T,2,min(len(L)+1,6))','E=_best_group_from_pool(T,2,min(len(L)+1,7))',1))
    # Low threshold probes repeatedly looked unstable; skip them in paced official loop.
    # Scarce structural probes: coverage penalty / risk drop only, preserving critical postprocessing.
    add('scarce_shadow_penalty80', s.replace('return C+60.*(len(I)-len(B))+14.*L+N+M/5.','return C+80.*(len(I)-len(B))+14.*L+N+M/5.',1))
    add('scarce_shadow_penalty100', s.replace('return C+60.*(len(I)-len(B))+14.*L+N+M/5.','return C+100.*(len(I)-len(B))+14.*L+N+M/5.',1))
    add('hard_scarce_top6', s.replace('D=sorted(A,key=lambda s:_solution_expected_cost(s,B,C))[:4];E=[]','D=sorted(A,key=lambda s:_solution_expected_cost(s,B,C))[:6];E=[]',1))
    add('hard_scarce_drop3', s.replace('G=_drop_riskiest_groups(A,B,2)\n\t\tif G:E.append(G)','G=_drop_riskiest_groups(A,B,2)\n\t\tif G:E.append(G)\n\t\tH=_drop_riskiest_groups(A,B,3)\n\t\tif H:E.append(H)',1))
    add('pair_rewire_pool9', s.replace('D=_best_group_from_pool(S,2,min(len(I)+1,6))','D=_best_group_from_pool(S,2,min(len(I)+3,9))',1).replace('E=_best_group_from_pool(T,2,min(len(L)+1,6))','E=_best_group_from_pool(T,2,min(len(L)+3,9))',1))
    add('pair_rewire_pool5_fast', s.replace('D=_best_group_from_pool(S,2,min(len(I)+1,6))','D=_best_group_from_pool(S,2,min(len(I)+1,5))',1).replace('E=_best_group_from_pool(T,2,min(len(L)+1,6))','E=_best_group_from_pool(T,2,min(len(L)+1,5))',1))
    # Tiny/small/high-noise MCF reassign time probe.
    add('fg_reassign_short', s.replace('if F and time.monotonic()<A-.34:\n\t\tK=_reassign_mixed_solution(D,C,B,min(A,time.monotonic()+.14))','if F and time.monotonic()<A-.28:\n\t\tK=_reassign_mixed_solution(D,C,B,min(A,time.monotonic()+.10))',1))
    add('fg_reassign_long', s.replace('if F and time.monotonic()<A-.34:\n\t\tK=_reassign_mixed_solution(D,C,B,min(A,time.monotonic()+.14))','if F and time.monotonic()<A-.42:\n\t\tK=_reassign_mixed_solution(D,C,B,min(A,time.monotonic()+.20))',1))
    random.Random(round_no).shuffle(variants)
    return variants

def local_eval(path,timeout=220):
    code=r'''
import importlib.machinery, importlib.util, json, sys, time, statistics
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72'); sys.path.insert(0,str(ROOT/'runs')); import proxy_eval
p=Path(sys.argv[1]); loader=importlib.machinery.SourceFileLoader('m'+str(abs(hash(str(p)))),str(p)); spec=importlib.util.spec_from_loader(loader.name,loader); m=importlib.util.module_from_spec(spec); loader.exec_module(m)
cases=[('large',(ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt').read_text(),1),('low025',proxy_eval.make_low(.25),1),('scarce40',proxy_eval.make_scarce(),2)]
rows=[]
for name,text,trials in cases:
 parsed,tasks,couriers=proxy_eval.parse(text); T=set(tasks); vals=[]; groups=[]; times=[]
 for _ in range(trials):
  t=time.monotonic(); r=m.solve(text); times.append(time.monotonic()-t); vals.append(m._solution_expected_cost(r,parsed,T)); groups.append(len(r))
 rows.append({'case':name,'mean':statistics.mean(vals),'best':min(vals),'worst':max(vals),'time':statistics.mean(times),'groups':groups,'vals':vals})
print(json.dumps(rows,ensure_ascii=False))
'''
    rc,out=sh([sys.executable,'-c',code,str(path)],timeout=timeout)
    if rc: return None
    return json.loads(out.strip().splitlines()[-1])

def score(rows):
    d={r['case']:r for r in rows}
    return (d['large']['mean']-657.104)*4 + (d['low025']['mean']-1891.05)*0.35 + (d['scarce40']['mean']-1097.85)*0.6 + max(0,d['large']['time']-9.1)*25 + max(0,d['scarce40']['time']-9.5)*20 + (35 if min(d['scarce40']['groups'])<39 else 0)

submitted=0
slots=next_slots(TARGET_REMAINING)
log('[start] paced loop; planned slots='+', '.join(x.strftime('%H:%M') for x in slots))
write_learning('Paced submission loop started', 'Planned slots: '+', '.join(x.strftime('%H:%M') for x in slots)+'. Will submit at most one candidate per slot after local preflight/cache checks.')
leader=[]; seen=set(); round_no=0; last_submit_time=None
while dt.datetime.now()<END and submitted<TARGET_REMAINING:
    round_no+=1
    known=official_shas_from_files()
    log(f'[round {round_no}] submitted={submitted}/{TARGET_REMAINING} next_slot={slots[submitted].strftime("%H:%M") if submitted<len(slots) else "none"}')
    def maybe_submit_due():
        nonlocal_vars = None
        return False

    for name,text in make_candidate(round_no):
        path=RUNS/f'paced_r{round_no}_{name}.py'
        path.write_text(text,encoding='utf-8')
        sha,size=sha_path(path)
        if sha in seen or sha in known:
            continue
        seen.add(sha)
        if size>=80000: continue
        rc,_=sh([sys.executable,'-m','py_compile',str(path)],timeout=30)
        if rc: continue
        rows=local_eval(path)
        if not rows: continue
        sc=score(rows)
        item={'score':sc,'name':name,'path':str(path),'sha':sha,'size':size,'rows':rows,'time':dt.datetime.now().isoformat(timespec='seconds')}
        leader.append(item); leader=sorted(leader,key=lambda x:x['score'])[:30]
        (RUNS/'paced_candidate_leaderboard_latest.json').write_text(json.dumps(leader,ensure_ascii=False,indent=2),encoding='utf-8')
        log(f'[candidate] {name} score={sc:.2f} sha={sha[:8]} rows='+json.dumps(rows,ensure_ascii=False))
        now=dt.datetime.now()
        due=submitted<len(slots) and now>=slots[submitted]
        spacing_ok=last_submit_time is None or (now-last_submit_time).total_seconds()>=SUBMIT_SPACING_MIN*60
        if due and spacing_ok:
            # Pick best not officially known, not already submitted by this loop.
            pick=None
            known=official_shas_from_files()
            for cand in leader:
                if cand['sha'] not in known:
                    pick=cand; break
            if pick:
                log(f'[official_planned_submit] slot={slots[submitted].strftime("%H:%M")} pick={pick["name"]} score={pick["score"]:.2f} sha={pick["sha"][:8]}')
                rc,out=sh([sys.executable,'runs/official_submit_safe.py','--solver',os.path.relpath(pick['path'],ROOT),'--note',f'paced submit {submitted+1}/12 {pick["name"]} sha {pick["sha"][:8]}'],timeout=700)
                last_submit_time=dt.datetime.now(); submitted+=1
                write_learning(f'Paced official submit {submitted}/12 completed', f'Candidate `{pick["name"]}`, sha `{pick["sha"]}`, rc `{rc}`. See latest official JSON and paced log.')
                break
    log('[leader_top] '+json.dumps(leader[:5],ensure_ascii=False))
    now=dt.datetime.now()
    due=submitted<len(slots) and now>=slots[submitted]
    spacing_ok=last_submit_time is None or (now-last_submit_time).total_seconds()>=SUBMIT_SPACING_MIN*60
    if due and spacing_ok:
        known=official_shas_from_files(); pick=None
        for cand in leader:
            if cand['sha'] not in known:
                pick=cand; break
        if pick:
            log(f'[official_planned_submit] slot={slots[submitted].strftime("%H:%M")} pick={pick["name"]} score={pick["score"]:.2f} sha={pick["sha"][:8]}')
            rc,out=sh([sys.executable,'runs/official_submit_safe.py','--solver',os.path.relpath(pick['path'],ROOT),'--note',f'paced submit {submitted+1}/12 {pick["name"]} sha {pick["sha"][:8]}'],timeout=700)
            last_submit_time=dt.datetime.now(); submitted+=1
            write_learning(f'Paced official submit {submitted}/12 completed', f'Candidate `{pick["name"]}`, sha `{pick["sha"]}`, rc `{rc}`. See latest official JSON and paced log.')
    if submitted<TARGET_REMAINING:
        sleep_s=120
        next_slot=slots[submitted] if submitted<len(slots) else END
        if dt.datetime.now()<next_slot:
            sleep_s=max(60,min(300,(next_slot-dt.datetime.now()).total_seconds()/3))
        log(f'[sleep] {sleep_s:.0f}s')
        time.sleep(sleep_s)
log('[done] paced loop ended')
