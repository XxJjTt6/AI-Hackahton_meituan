#!/usr/bin/env python3
import json, subprocess, sys, time, hashlib
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
base=(ROOT/'solver.py').read_text()
RUNS=ROOT/'runs'

def make(name,text):
    p=RUNS/f'guard_{name}.py'; p.write_text(text); return p

def evalp(p):
    code=r'''
import importlib.machinery, importlib.util, sys, json, statistics, time
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72'); sys.path.insert(0,str(ROOT/'runs')); import proxy_eval
p=Path(sys.argv[1]); loader=importlib.machinery.SourceFileLoader('m',str(p)); spec=importlib.util.spec_from_loader('m',loader); m=importlib.util.module_from_spec(spec); loader.exec_module(m)
cases=[('large',(ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt').read_text(),2),('low025',proxy_eval.make_low(.25),4),('scarce40',proxy_eval.make_scarce(),8)]
rows=[]
for name,text,trials in cases:
 parsed,tasks,couriers=proxy_eval.parse(text); T=set(tasks); vals=[]; groups=[]; times=[]
 for _ in range(trials):
  t=time.monotonic(); r=m.solve(text); times.append(time.monotonic()-t); vals.append(m._solution_expected_cost(r,parsed,T)); groups.append(len(r))
 rows.append({'case':name,'mean':statistics.mean(vals),'best':min(vals),'worst':max(vals),'groups':groups,'time':statistics.mean(times),'vals':vals})
print(json.dumps(rows,ensure_ascii=False))
'''
    out=subprocess.check_output([sys.executable,'-c',code,str(p)],cwd=ROOT,text=True,timeout=520)
    return json.loads(out.strip().splitlines()[-1])

variants=[]
variants.append(('no_drop_risky', base.replace("D=sorted(A,key=lambda s:_solution_expected_cost(s,B,C))[:4];E=[]\n\tfor A in D:\n\t\tE.append(A);F=_drop_riskiest_groups(A,B,1)\n\t\tif F:E.append(F)\n\t\tG=_drop_riskiest_groups(A,B,2)\n\t\tif G:E.append(G)\n\treturn min(E,key=lambda s:(_hard_scarce_shadow_cost(s,B,C),_solution_expected_cost(s,B,C)))", "D=sorted(A,key=lambda s:_solution_expected_cost(s,B,C))[:6]\n\treturn min(D,key=lambda s:(_hard_scarce_shadow_cost(s,B,C),_solution_expected_cost(s,B,C)))",1)))
variants.append(('strong_uncovered_penalty', base.replace('return C+60.*(len(I)-len(B))+14.*L+N+M/5.', 'return C+180.*(len(I)-len(B))+14.*L+N+M/5.',1)))
variants.append(('no_drop_plus_penalty', variants[0][1].replace('return C+60.*(len(I)-len(B))+14.*L+N+M/5.', 'return C+180.*(len(I)-len(B))+14.*L+N+M/5.',1)))
variants.append(('pick_by_coverage_then_shadow', base.replace('return min(E,key=lambda s:(_hard_scarce_shadow_cost(s,B,C),_solution_expected_cost(s,B,C)))', 'M=max(_solution_covered_count(s,B)for s in E)\n\tE=[s for s in E if _solution_covered_count(s,B)>=M]\n\treturn min(E,key=lambda s:(_hard_scarce_shadow_cost(s,B,C),_solution_expected_cost(s,B,C)))',1)))
for name,text in variants:
    p=make(name,text)
    subprocess.check_call([sys.executable,'-m','py_compile',str(p)],cwd=ROOT)
    b=p.read_bytes(); sha=hashlib.sha256(b).hexdigest()
    print(f'[guard_candidate] {name} sha={sha[:8]} size={len(b)}',flush=True)
    rows=evalp(p)
    print(json.dumps({'name':name,'sha':sha,'rows':rows},ensure_ascii=False),flush=True)
