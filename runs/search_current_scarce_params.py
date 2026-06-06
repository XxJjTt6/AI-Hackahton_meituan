#!/usr/bin/env python3
from pathlib import Path
import subprocess, json, re, os, hashlib, sys, textwrap
ROOT=Path(__file__).resolve().parents[1]
base=(ROOT/'solver.py').read_text()
variants=[]
configs=[
 ('seed4_prune900_beam3600_alns_less', {'J8':'J[:4]','prune':'900','beam':'3600','alns':"if time.monotonic()<D-.65:A=_column_alns_repair_solution(A,B,C,min(D,time.monotonic()+.52),mode=_J,max_window_tasks=10,top_riders_per_task_key=7,option_limit=45,max_k=3);A=_drop_unprofitable_groups(A,B,C)"}),
 ('seed4_prune1500_beam6200', {'J8':'J[:4]','prune':'1500','beam':'6200'}),
 ('seed12_prune1500_beam6200', {'J8':'J[:12]','prune':'1500','beam':'6200'}),
 ('seed8_prune1800_beam7200', {'J8':'J[:8]','prune':'1800','beam':'7200'}),
 ('seed4_alns_less_only', {'J8':'J[:4]','alns':"if time.monotonic()<D-.65:A=_column_alns_repair_solution(A,B,C,min(D,time.monotonic()+.52),mode=_J,max_window_tasks=10,top_riders_per_task_key=7,option_limit=45,max_k=3);A=_drop_unprofitable_groups(A,B,C)"}),
]
for name,cfg in configs:
 s=base
 if 'J8' in cfg: s=s.replace('J[:8]',cfg['J8'])
 if 'prune' in cfg: s=s.replace('max_columns=1150',f"max_columns={cfg['prune']}")
 if 'beam' in cfg: s=s.replace('beam_width=5200',f"beam_width={cfg['beam']}")
 if 'alns' in cfg:
  old="if time.monotonic()<D-.85:A=_column_alns_repair_solution(A,B,C,min(D,time.monotonic()+.75),mode=_J,max_window_tasks=12,top_riders_per_task_key=8,option_limit=55,max_k=4);A=_drop_unprofitable_groups(A,B,C)"
  s=s.replace(old,cfg['alns'])
 p=ROOT/'runs'/f'param_{name}.py'; p.write_text(s); variants.append(p)
for p in variants:
 print('###',p.name,os.path.getsize(p),hashlib.sha256(p.read_bytes()).hexdigest()[:8],flush=True)
 r=subprocess.run([sys.executable,'runs/proxy_eval.py','solver.py',str(p.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True,timeout=120)
 print(r.stdout[-2500:],flush=True)
