#!/usr/bin/env python3
import importlib.util, time, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据'/'large_seed301.txt'

def load(path):
    spec=importlib.util.spec_from_file_location('sol', str(path)); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def parse(text):
    lines=text.strip().splitlines();
    if lines and lines[0].startswith('task_id'): lines=lines[1:]
    c=[]; tasks=set()
    for i,ln in enumerate(lines):
        p=ln.split('\t')
        if len(p)<4: continue
        task=p[0].strip(); ts=tuple(x.strip() for x in task.split(',') if x.strip()); cid=p[1].strip()
        try: score=float(p[2]); will=float(p[3])
        except: continue
        c.append((task,ts,cid,score,will,i)); tasks.update(ts)
    return c,tasks

def signature(out):
    s='\n'.join(f'{k}:{",".join(v)}' for k,v in out)
    return hashlib.sha256(s.encode()).hexdigest()[:16]

def kdist(out):
    d={}
    for k,v in out:
        d[len(v)]=d.get(len(v),0)+1
    return d

def main():
    mod=load(ROOT/'solver.py')
    text=DATA.read_text(); c,t=parse(text)
    for i in range(3):
        t0=time.monotonic(); out=mod.solve(text); dt=time.monotonic()-t0
        print({'trial':i+1,'time':round(dt,3),'proxy':round(mod._solution_expected_cost(out,c,t),6),'min_score':round(mod._solution_expected_cost_by_model(out,c,t,'min_score'),6),'max_will':round(mod._solution_expected_cost_by_model(out,c,t,'max_willingness'),6),'groups':len(out),'kdist':kdist(out),'sig':signature(out)})
if __name__=='__main__': main()
