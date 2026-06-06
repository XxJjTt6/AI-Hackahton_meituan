import importlib.util, time, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=[ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt',ROOT/'runs/synth_medium_from_large301_30x60.txt',ROOT/'runs/synth_scarce_large301_40x40.txt',ROOT/'runs/official_like_low_synth.txt']
spec=importlib.util.spec_from_file_location('s',ROOT/'solver.py'); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
def parse(text):
    lines=text.strip().splitlines(); start=1 if lines and lines[0].startswith('task') else 0
    C=[];B=set()
    for idx,line in enumerate(lines[start:]):
        p=line.split('\t')
        if len(p)<4: continue
        key,cid,sc,w=p[:4]; tasks=tuple(x.strip() for x in key.split(',') if x.strip())
        C.append((key,tasks,cid,float(sc),float(w),idx)); B.update(tasks)
    return C,B
ops=[
 ('repair12',lambda D,C,B,dl:s._repair_worst_window_solution(D,C,B,dl,top_riders_per_task_key=12,max_k=4,option_limit=100)),
 ('alns_norm',lambda D,C,B,dl:s._column_alns_repair_solution(D,C,B,dl,mode='normal',max_window_tasks=12,top_riders_per_task_key=10,option_limit=90,max_k=4)),
 ('pair48',lambda D,C,B,dl:s._pairwise_column_exchange_solution(D,C,B,dl,top_riders_per_task_key=10,max_k=4,option_limit=90,max_window_tasks=12,max_pairs=48)),
 ('triple24',lambda D,C,B,dl:s._triple_column_exchange_solution(D,C,B,dl,top_riders_per_task_key=10,max_k=4,option_limit=90,max_window_tasks=12,max_triples=24)),
 ('reassign',lambda D,C,B,dl:s._reassign_mixed_solution(D,C,B,dl)),
]
for path in DATA:
    if not path.exists(): continue
    text=path.read_text(); C,B=parse(text); D=s.solve(text); base=s._solution_expected_cost(D,C,B)
    best=D; bc=base; hist=[]; start=time.monotonic();
    for r in range(4):
        improved=False
        for name,op in ops:
            dl=time.monotonic()+0.8
            cand=op(best,C,B,dl)
            cc=s._solution_expected_cost(cand,C,B)
            if cc<bc-1e-9:
                hist.append((r,name,bc,cc,bc-cc)); best=cand; bc=cc; improved=True
        if not improved: break
    covered=set(); row={(x[0],x[2]):x for x in C}
    for k,ls in best:
        rr=row.get((k,ls[0])) if ls else None
        if rr: covered.update(rr[1])
    print(json.dumps({'case':path.name,'base':base,'best':bc,'delta':bc-base,'groups':len(best),'covered':len(covered),'hist':hist,'time':time.monotonic()-start},ensure_ascii=False))
