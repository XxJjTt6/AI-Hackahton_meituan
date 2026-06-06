import importlib.util,sys,json
from pathlib import Path
inp=Path('Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt').read_text()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
base=load('solver.py','base'); cand=load('runs/candidate_penalty80.py','cand')
for name,mod in [('base',base),('p80',cand)]:
    out=mod.solve(inp); print(name,'groups',len(out),'shape',sorted(__import__('collections').Counter(len(x[1]) for x in out).items()))
    print(out[:5])
print('same?', base.solve(inp)==cand.solve(inp))
