#!/usr/bin/env python3
from __future__ import annotations
import subprocess, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CASES=[
 ('large','Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt'),
 ('low_cal','runs/official_calibrated_low_synth.txt'),
 ('low_like','runs/official_like_low_synth.txt'),
 ('medium_synth','runs/synth_medium_from_large301_30x60.txt'),
 ('scarce_synth','runs/synth_scarce_large301_40x40.txt'),
]
COMMANDS=[]
for name,path in CASES:
    if name in ('large','medium_synth'):
        for sec in (4,8):
            COMMANDS.append((name,'bundle_redist', ['python3','runs/prototype_bundle_redundancy_exchange.py',path,'--seconds',str(sec)]))
            COMMANDS.append((name,'augment', ['python3','runs/prototype_augmenting_path_exchange.py',path,'--seconds',str(sec),'--depth','4','--branch','16']))
    if name.startswith('low'):
        for seed in (4,5,6):
            COMMANDS.append((name,f'low_sa_{seed}', ['python3','runs/prototype_low_k2_swap_sa.py',path,'--seconds','5','--seed',str(seed)]))
        COMMANDS.append((name,'dual_master', ['python3','runs/prototype_dual_priced_master.py',path,'--max-columns','420','--seconds','4','--nodes','50000']))
    if name=='scarce_synth':
        COMMANDS.append((name,'scarce_pack', ['python3','runs/prototype_scarce_set_packing.py',path,'--max-k','2','--top-rows','10','--max-columns','1800','--beam','4000']))
        COMMANDS.append((name,'scarce_probe', ['python3','runs/probe_401_unobserved_candidates_from_synth.py',path]))

out=ROOT/'runs/local_prototype_sweep_20260522.txt'
with out.open('w') as fh:
    for i,(case,label,cmd) in enumerate(COMMANDS,1):
        start=time.monotonic()
        fh.write(f'\n=== {i}/{len(COMMANDS)} {case} {label} ===\n$ {" ".join(cmd)}\n'); fh.flush()
        try:
            proc=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45)
            fh.write(proc.stdout)
            fh.write(f'EXIT={proc.returncode} elapsed={time.monotonic()-start:.2f}s\n')
        except subprocess.TimeoutExpired as e:
            fh.write((e.stdout or '') if isinstance(e.stdout,str) else '')
            fh.write(f'TIMEOUT elapsed={time.monotonic()-start:.2f}s\n')
        fh.flush()
print(out)
