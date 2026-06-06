import importlib.util,collections
from pathlib import Path
inp=Path('Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt').read_text()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
base=load('solver.py','b'); p80=load('runs/candidate_p80_fast_global.py','p')
b=base.solve(inp); q=p80.solve(inp)
bd={k:tuple(v) for k,v in b}; qd={k:tuple(v) for k,v in q}
print('changed tasks',sum(1 for k in bd if bd[k]!=qd.get(k)))
for k in sorted(bd):
    if bd[k]!=qd.get(k): print(k,'base',bd[k],'p80',qd.get(k))
