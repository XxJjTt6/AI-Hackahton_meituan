#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys, re
base=Path('solver.py').read_text()
variants=[]
repls=[
('normal_repair_opt70', 'option_limit=55,max_k=3)', 'option_limit=70,max_k=3)'),
('normal_repair_top10', 'top_riders_per_task_key=8,option_limit=55,max_k=3)', 'top_riders_per_task_key=10,option_limit=55,max_k=3)'),
('normal_pair_more', 'max_pairs=32)', 'max_pairs=48)'),
('normal_triple_more', 'max_triples=16)', 'max_triples=24)'),
('random_single_less', 'S=900 if len(A)>=35 else 350', 'S=650 if len(A)>=35 else 350'),
('random_single_more', 'S=900 if len(A)>=35 else 350', 'S=1200 if len(A)>=35 else 350'),
]
for name,old,new in repls:
    s=base.replace(old,new,1)
    p=Path('runs')/(name+'.py'); p.write_text(s); variants.append(str(p))
for p in variants:
    subprocess.run(['python3','-m','py_compile',p],check=True)
    out=subprocess.check_output(['python3','runs/cross_score_eval.py','solver.py',p],text=True,timeout=35)
    m=re.findall(r'cand own [^\n]*base_score ([0-9.]+)',out)
    b=re.findall(r'base own ([0-9.]+)',out)
    print('\n##',p)
    print(out.strip())
