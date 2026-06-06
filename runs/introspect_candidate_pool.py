#!/usr/bin/env python3
# Lightweight monkeypatch introspection: collect final candidate list E at pick sites is hard in minified code;
# instead compare output under model variants by patching picker functions after import for public/calibrated cases.
import sys, importlib.machinery, importlib.util, time, hashlib
from pathlib import Path
sys.path.insert(0,'runs')
import proxy_eval

def load(path):
    name='introspect_'+str(abs(hash(path)))
    loader=importlib.machinery.SourceFileLoader(name,path); spec=importlib.util.spec_from_loader(name,loader)
    mod=importlib.util.module_from_spec(spec); loader.exec_module(mod); return mod

def sig(res): return hashlib.sha256('\n'.join(f'{k}:{",".join(cs)}' for k,cs in res).encode()).hexdigest()[:12]

def eval_case(text_path):
    text=Path(text_path).read_text() if text_path else proxy_eval.DATA.read_text()
    print('\nCASE',text_path or 'large_seed301')
    for variant in ['safe','low_min_only','low_max_only','scarce_cost_only']:
        mod=load('solver.py')
        if variant=='low_min_only':
            def pick(solutions,candidates,all_tasks):
                arr=[s for s in solutions if s]
                return min(arr,key=lambda s: mod._solution_expected_cost_by_model(s,candidates,all_tasks,mod._L)) if arr else []
            mod._pick_low_robust_best=pick
        elif variant=='low_max_only':
            def pick(solutions,candidates,all_tasks):
                arr=[s for s in solutions if s]
                return min(arr,key=lambda s: mod._solution_expected_cost_by_model(s,candidates,all_tasks,mod._M)) if arr else []
            mod._pick_low_robust_best=pick
        elif variant=='scarce_cost_only':
            def pick(solutions,candidates,all_tasks):
                arr=[s for s in solutions if s]
                return min(arr,key=lambda s: mod._solution_expected_cost(s,candidates,all_tasks)) if arr else []
            mod._pick_hard_scarce_best=pick
        rows,tasks,couriers=proxy_eval.parse(text); t=time.monotonic(); res=mod.solve(text); dt=time.monotonic()-t
        print(variant,'cost',round(mod._solution_expected_cost(res,rows,set(tasks)),6),'time',round(dt,3),'sig',sig(res),'k',{j:sum(len(cs)==j for _,cs in res) for j in range(1,6)},'n',len(res))

for p in [None,'runs/official_calibrated_low_synth.txt','runs/official_like_low_synth.txt']:
    eval_case(p)
