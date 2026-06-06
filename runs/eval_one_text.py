#!/usr/bin/env python3
import sys,time,hashlib
from pathlib import Path
sys.path.insert(0,'runs')
import proxy_eval
solver_path=sys.argv[1]; text_path=sys.argv[2]
mod=proxy_eval.load(solver_path); text=Path(text_path).read_text(); rows,tasks,couriers=proxy_eval.parse(text)
t=time.monotonic(); res=mod.solve(text); dt=time.monotonic()-t
cost=mod._solution_expected_cost(res,rows,set(tasks)); sig=hashlib.sha256('\n'.join(f'{k}:{",".join(cs)}' for k,cs in res).encode()).hexdigest()[:12]
print(solver_path,Path(text_path).name,'cost',round(cost,6),'time',round(dt,3),'n',len(res),'k',{j:sum(len(cs)==j for _,cs in res) for j in range(1,6)},'sig',sig)
for x in res[:10]: print(' ',x)
