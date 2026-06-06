import importlib.util,collections,sys
from pathlib import Path
inp=Path('Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt').read_text()
for path in ['solver.py','runs/candidate_penalty70.py','runs/candidate_penalty80.py','runs/candidate_penalty90.py']:
    spec=importlib.util.spec_from_file_location('m'+path.replace('/','_').replace('.','_'),path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    out=m.solve(inp); shape=collections.Counter(len(x[1]) for x in out)
    print('\n',path,'shape',sorted(shape.items()))
    for row in out: print(row)
