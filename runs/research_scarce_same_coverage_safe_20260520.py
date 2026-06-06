#!/usr/bin/env python3
# Public/proxy same-coverage optimizer: never touches T0033 family directly; test if same covered-set cost reduction exists.
import importlib.util,pathlib,time,itertools,sys
ROOT=pathlib.Path.cwd(); spec=importlib.util.spec_from_file_location('s',ROOT/'solver.py'); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
# Use proxy_eval scarce generator because official input is unavailable.
sys.path.insert(0,str(ROOT/'runs')); import proxy_eval
text=proxy_eval.make_scarce(); C,tasks,couriers=proxy_eval.parse(text); B=set(tasks)
base=s.solve(text); row={(r[0],r[2]):r for r in C}; sel=s._result_to_selected(base,row); basecost=s._solution_expected_cost(base,C,B)
covered={t for rows in sel.values() for t in rows[0][1]}
print('base',basecost,'groups',len(base),'covered',len(covered))
# Build candidate columns restricted to subsets of currently covered tasks only, no new uncovered task target.
covered_set=set(covered); used_tasks_target=covered_set
cols=[]
task_index={t:i for i,t in enumerate(sorted(used_tasks_target))}; courier_index={c:i for i,c in enumerate(sorted({r[2] for r in C}))}
for r in s._canonical_candidates(C):
    if not set(r[1]) <= used_tasks_target: continue
    if len(r[1])>2: continue
    cost=s._group_expected_cost([r],len(r[1])); saving=100*len(r[1])-cost
    if saving<=0: continue
    tmask=0
    for t in r[1]: tmask|=1<<task_index[t]
    cmask=1<<courier_index[r[2]]
    cols.append((cost,tmask,cmask,r))
cols.sort(key=lambda x:(x[0]/max(1,x[1].bit_count()),x[0]))
# Beam set partition to exactly cover current covered tasks with no courier reuse.
target=(1<<len(task_index))-1
states={0:(0.0,0,())}; limit=5000; deadline=time.monotonic()+5
for cost,tmask,cmask,r in cols[:2000]:
    if time.monotonic()>deadline: break
    new=dict(states)
    for mask,(val,used,path) in list(states.items()):
        if mask&tmask or used&cmask: continue
        nm=mask|tmask; nv=val+cost
        old=new.get(nm)
        if old is None or nv<old[0]: new[nm]=(nv,used|cmask,path+(r,))
    if len(new)>limit:
        new=dict(sorted(new.items(), key=lambda kv:(-(kv[0].bit_count()),kv[1][0]))[:limit])
    states=new
best=states.get(target)
if best:
    cost,used,path=best; out=[(r[0],[r[2]]) for r in path]; print('best samecov',cost,'delta',cost-basecost,'groups',len(out),'covered',len({t for r in path for t in r[1]}))
else: print('no exact same coverage')
