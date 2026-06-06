#!/usr/bin/env python3
import argparse, hashlib, json, glob, sys
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
SAFE_SHA='70222083707d786011d28d7cc1ceab8f3b2ca95e0924b26f8dff2e6a49e865d6'
BLACK={'ac55cf9c':'global p80 negative','af88b6fc':'high guard scarce regression','60cf6691':'compact cache hidden large302 collision','52daa29b':'compact high patch did not trigger and scarce regressed official 712.2072','0fc08e17':'T0033 replacement/window route official scarce regression to 1571.9010','97eced0c':'seed401 missing-task swap/split official regression to 1589.3393'}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('solver'); ap.add_argument('--expected-avg-gain',type=float,required=True); ap.add_argument('--structural',action='store_true')
    a=ap.parse_args(); data=Path(a.solver).read_bytes(); sha=hashlib.sha256(data).hexdigest()
    print('sha',sha,'size',len(data),'expected_gain',a.expected_avg_gain,'structural',a.structural)
    if len(data)>=80000: sys.exit('REJECT size >=80KB')
    if sha.startswith(tuple(BLACK)): sys.exit('REJECT blacklisted sha prefix')
    text=data.decode('utf-8', errors='ignore')
    if '_row_cache' in text or 'candidate_compact_cache' in str(a.solver):
        sys.exit('REJECT compact row-cache family: official 60cf6691 hidden collision')
    solver_name=str(a.solver).lower()
    if 't0033' in solver_name or 'uncovered_window' in solver_name:
        sys.exit('REJECT T0033/uncovered-window family: official 0fc08e17 scarce regression')
    if 'missing_swap' in solver_name or 'missing-task swap' in text or 'swap/split repair' in text:
        sys.exit('REJECT seed401 missing-task swap/split family: official 97eced0c scarce regression')
    if 'low_k2' in solver_name and not a.structural:
        sys.exit('REJECT low_k2 family unless explicitly marked structural and >= threshold')
    if a.expected_avg_gain<1.0 and not a.structural: sys.exit('REJECT below user threshold')
    print('PASS policy only; still run preflight before submit')
if __name__=='__main__': main()
