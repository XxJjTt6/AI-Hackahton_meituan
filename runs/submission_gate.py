#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'runs/baselines/official_best_70222083.py'
PROXIES = [
    ROOT / 'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt',
    ROOT / 'runs/official_calibrated_low_synth.txt',
    ROOT / 'runs/official_like_low_synth.txt',
    ROOT / 'runs/synth_medium_from_large301_30x60.txt',
    ROOT / 'runs/synth_scarce_large301_40x40.txt',
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_json(cmd):
    proc = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=80)
    if proc.returncode != 0:
        raise SystemExit(proc.stdout)
    return proc.stdout


def main():
    parser = argparse.ArgumentParser(description='Local gate before considering official submission.')
    parser.add_argument('candidate')
    parser.add_argument('--allow-noop', action='store_true')
    args = parser.parse_args()
    candidate = (ROOT / args.candidate).resolve() if not Path(args.candidate).is_absolute() else Path(args.candidate)
    raw = candidate.read_bytes()
    print('candidate', candidate)
    print('size', len(raw), 'sha256', sha(candidate))
    if len(raw) >= 80000:
        raise SystemExit('REJECT size >= 80000')
    subprocess.run([sys.executable, '-m', 'py_compile', str(candidate)], cwd=ROOT, check=True)
    any_change = False
    any_bad = False
    for proxy in PROXIES:
        if not proxy.exists():
            continue
        out = ROOT / 'runs' / f'_gate_{candidate.stem}_{proxy.stem}.json'
        subprocess.run([sys.executable, '-m', 'autosolver.competition_audit', str(BASELINE), str(candidate), str(proxy), '--output', str(out)], cwd=ROOT, check=True, timeout=90)
        data = json.loads(out.read_text())
        delta = data['delta_expected_cost']
        same = data['same_signature']
        cov_delta = data['delta_covered_tasks']
        print(proxy.name, 'same', same, 'delta', round(delta, 9), 'cov_delta', cov_delta)
        if not same or abs(delta) > 1e-9 or cov_delta != 0:
            any_change = True
        if delta > 1e-9 or cov_delta < 0:
            any_bad = True
    if any_bad:
        raise SystemExit('REJECT proxy regression detected')
    if not any_change and not args.allow_noop:
        raise SystemExit('REJECT no proxy/signature change; official submit would be low-information')
    print('PASS local gate; still require human/strategy approval before official submit')


if __name__ == '__main__':
    main()
