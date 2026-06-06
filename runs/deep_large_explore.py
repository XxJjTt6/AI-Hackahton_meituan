import importlib.util, time, collections
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'
spec=importlib.util.spec_from_file_location('s', ROOT/'solver.py')
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
text=DATA.read_text()
# parse same as solver by invoking solve then rebuilding rows
def parse(text):
    lines=text.strip().splitlines(); start=1 if lines and lines[0].startswith('task') else 0
    rows=[]; tasks=set()
    for i,ln in enumerate(lines[start:]):
        p=ln.split('\t')
        if len(p)<4: continue
        key,c,sc,w=p[:4]; ts=tuple(x.strip() for x in key.split(',') if x.strip())
        if not ts: continue
        rows.append((key,ts,c,float(sc),float(w),i)); tasks.update(ts)
    return rows,set(tasks)
rows,tasks=parse(text)
t0=time.monotonic(); res=s.solve(text); print('base solve',time.monotonic()-t0,s._solution_expected_cost(res,rows,tasks),len(res),s._solution_covered_count(res,rows),collections.Counter(len(c) for _,c in res), flush=True)
best=res; bestc=s._solution_expected_cost(best,rows,tasks)
def tryit(name, fn):
    global best,bestc
    t=time.monotonic(); cand=fn(best, time.monotonic()+20.0); c=s._solution_expected_cost(cand,rows,tasks); cov=s._solution_covered_count(cand,rows)
    print(name,'dt',time.monotonic()-t,'cost',c,'delta',c-bestc,'cov',cov,'groups',len(cand),collections.Counter(len(cs) for _,cs in cand), flush=True)
    if cov>=s._solution_covered_count(best,rows) and c<bestc-1e-9:
        best,bestc=cand,c; print('  ACCEPT',bestc, flush=True)
for r in range(3):
    tryit(f'worst{r}', lambda b,d: s._repair_worst_window_solution(b,rows,tasks,d,top_riders_per_task_key=14,max_k=5,option_limit=160))
    tryit(f'alns{r}', lambda b,d: s._column_alns_repair_solution(b,rows,tasks,d,mode='normal',max_window_tasks=14,top_riders_per_task_key=14,option_limit=160,max_k=5))
    tryit(f'pair{r}', lambda b,d: s._pairwise_column_exchange_solution(b,rows,tasks,d,top_riders_per_task_key=14,max_k=5,option_limit=160,max_window_tasks=14,max_pairs=200))
    tryit(f'triple{r}', lambda b,d: s._triple_column_exchange_solution(b,rows,tasks,d,top_riders_per_task_key=14,max_k=5,option_limit=180,max_window_tasks=16,max_triples=160))
    tryit(f'reassign{r}', lambda b,d: s._reassign_mixed_solution(b,rows,tasks,d))
print('final',bestc, 'delta vs base', bestc-s._solution_expected_cost(res,rows,tasks))
