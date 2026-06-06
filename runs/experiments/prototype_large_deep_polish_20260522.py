#!/usr/bin/env python3
import importlib.util,pathlib,time,random
ROOT=pathlib.Path(__file__).resolve().parents[2]
SOLVER=ROOT/'runs/baselines/official_best_7046558e_robust_cache.py'
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt'
spec=importlib.util.spec_from_file_location('s',SOLVER); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
text=DATA.read_text(); rows=[]; tasks=set()
for i,ln in enumerate(text.strip().splitlines()[1:]):
 p=ln.split('\t'); tl=tuple(x.strip() for x in p[0].split(',') if x.strip()); rows.append((p[0],tl,p[1],float(p[2]),float(p[3]),i)); tasks.update(tl)
sol=s.solve(text); best=sol; bestc=s._solution_expected_cost(sol,rows,tasks)
print('start',bestc, flush=True)
dead=time.monotonic()+120
iters=0
while time.monotonic()<dead:
    old=bestc
    for name,fn,args in [
        ('normal',s._normal_worst_related_repair_solution,(best,rows,tasks,min(dead,time.monotonic()+1.2))),
        ('alns',s._column_alns_repair_solution,(best,rows,tasks,min(dead,time.monotonic()+1.5),'normal',16,16,160,5)),
        ('pair',s._pairwise_column_exchange_solution,(best,rows,tasks,min(dead,time.monotonic()+1.2),16,5,160,16,80)),
        ('triple',s._triple_column_exchange_solution,(best,rows,tasks,min(dead,time.monotonic()+1.2),16,5,160,18,40)),
        ('reassign',s._reassign_mixed_solution,(best,rows,tasks,min(dead,time.monotonic()+.8))),
        ('local',s._local_improve_mixed_solution,(best,rows,tasks,min(dead,time.monotonic()+.8),True)),
    ]:
        cand=fn(*args)
        c=s._solution_expected_cost(cand,rows,tasks)
        iters+=1
        if c<bestc-1e-9:
            best,bestc=cand,c
            print('improve',name,bestc,'delta',bestc-old,'iter',iters,'tleft',dead-time.monotonic(), flush=True)
            break
    else:
        print('round no improve',iters,'best',bestc,'tleft',dead-time.monotonic(), flush=True)
        # try stochastic restarts using existing solve maybe deterministic no
        if iters>60: break
print('final',bestc,'delta',bestc-s._solution_expected_cost(sol,rows,tasks), 'groups',len(best), 'couriers',sum(len(c) for _,c in best), flush=True)
for g in sorted(best): print(g)
