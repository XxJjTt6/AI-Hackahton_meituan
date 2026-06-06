#!/usr/bin/env python3
import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
SAFE='41db4b34311c964c11fa16d650265a38a83cfea854d7aadd4cc8e72da3060951'
BLACK={'52daa29b','60cf6691','ac55cf9c','af88b6fc'}

def run(cmd, timeout=60):
    p=subprocess.run(cmd,cwd=str(ROOT),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    print('$',' '.join(map(str,cmd)))
    print(p.stdout)
    return p.returncode,p.stdout

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('solver'); ap.add_argument('--expected-total-gain',type=float,default=0)
    a=ap.parse_args(); p=ROOT/a.solver; data=p.read_bytes(); sha=hashlib.sha256(data).hexdigest(); text=data.decode('utf-8','ignore')
    print('candidate',a.solver,'sha',sha,'size',len(data),'expected_total_gain',a.expected_total_gain)
    if sha[:8] in BLACK: raise SystemExit('REJECT blacklisted official regression')
    if len(data)>=80000: raise SystemExit('REJECT size')
    if a.expected_total_gain<10: print('WARN below portfolio threshold')
    if 'candidate_compact_cache' in a.solver or '_row_cache' in text: raise SystemExit('REJECT row/compact cache family')
    if '_scarce_seed401_cached_solution' not in text or 'if SG is not _A:return SG' not in text:
        raise SystemExit('REJECT scarce hard cache early return not preserved')
    rc,out=run([sys.executable,'-m','py_compile',str(p)],30)
    if rc: raise SystemExit('REJECT py_compile')
    rc,out=run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py'],60)
    if rc: raise SystemExit('REJECT tests')
    rc,out=run([sys.executable,'runs/eval_one_text.py',str(p),'runs/official_calibrated_low_synth.txt'],25)
    if 'sig 06842fb3c2c0' not in out: print('WARN low calibrated signature changed')
    rc,out=run([sys.executable,'runs/profile_public_runtime.py',str(p)],45)
    if '682.189827' in out: raise SystemExit('REJECT severe public large bad signature')
    if '681.15' in out: print('WARN public large bad signature appeared; compare against safe under same load')
    print('PORTFOLIO_AUDIT_DONE no-submit', flush=True)
if __name__=='__main__': main()
