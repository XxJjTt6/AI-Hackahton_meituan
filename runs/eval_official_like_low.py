#!/usr/bin/env python3
import sys,time,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
text=(ROOT/'runs/official_like_low_synth.txt').read_text(); rows,tasks,c=proxy_eval.parse(text); T=set(tasks)
for arg in sys.argv[1:] or ['solver.py']:
    spec=importlib.util.spec_from_file_location('m'+str(abs(hash(arg))), str(ROOT/arg)); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    vals=[]
    for i in range(2):
        t=time.monotonic(); out=m.solve(text); vals.append((m._solution_expected_cost(out,rows,T),time.monotonic()-t,len(out),{k:sum(1 for _,cs in out if len(cs)==k) for k in sorted({len(cs) for _,cs in out})}))
    print(arg, vals)
