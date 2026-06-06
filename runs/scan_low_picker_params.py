#!/usr/bin/env python3
from pathlib import Path
import subprocess, re, json, sys
ROOT=Path(__file__).resolve().parents[1]
base=(ROOT/'solver.py').read_text()
orig="""\tdef G(solution):E=solution;D=_solution_expected_cost(E,A,B);F=_solution_expected_cost_by_model(E,A,B,_L);G=_solution_expected_cost_by_model(E,A,B,_M);H=.45*D+.45*F+.1*G;I=max(D-C,F-C,G-C);return H+.15*max(_C,I),max(D,F,G),D\n\tF=min(D,key=G);H=_solution_expected_cost(F,A,B)\n\tif H<=C+25.:return F\n\treturn E"""
variants=[
('base_equiv','.45','.45','.1','.15','25.'),
('strict5','.45','.45','.1','.15','5.'),
('minheavy','.35','.55','.1','.15','15.'),
('willheavy','.40','.35','.25','.15','15.'),
('regret30','.42','.48','.1','.30','15.'),
('relaxed40','.45','.45','.1','.15','40.'),
]
summary=[]
for name,w1,w2,w3,pen,thr in variants:
    p=ROOT/'runs'/f'low_picker_{name}.py'
    new=f"""\tdef G(solution):E=solution;D=_solution_expected_cost(E,A,B);F=_solution_expected_cost_by_model(E,A,B,_L);G=_solution_expected_cost_by_model(E,A,B,_M);H={w1}*D+{w2}*F+{w3}*G;I=max(D-C,F-C,G-C);return H+{pen}*max(_C,I),max(D,F,G),D\n\tF=min(D,key=G);H=_solution_expected_cost(F,A,B)\n\tif H<=C+{thr}:return F\n\treturn E"""
    if orig not in base: raise SystemExit('orig not found')
    p.write_text(base.replace(orig,new,1))
    out=subprocess.check_output([sys.executable, str(ROOT/'runs/proxy_eval.py'), str(p.relative_to(ROOT))], text=True)
    summary.append((name,out))
    print('###',name); print(out)
(Path(ROOT/'runs/low_picker_scan_0235.txt')).write_text('\n'.join('### '+n+'\n'+o for n,o in summary))
