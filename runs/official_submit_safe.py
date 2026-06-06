#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path('/Users/比赛/FOR_AutoSolver_706.72')
BASE = 'https://hackathon.mykeeta.com'
TOKEN = '13900139080'
TEAM = '料事如神'

def request_json(method, path, payload=None, timeout=30, tries=5):
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    headers = {'Content-Type': 'application/json'} if payload is not None else {}
    last = None
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as exc:
            last = exc
            print(f'[net_retry] {method} {path} attempt={attempt}/{tries} err={exc!r}', flush=True)
            time.sleep(min(2 * attempt, 10))
    raise last

def run(cmd, timeout=120):
    print('$', ' '.join(cmd), flush=True)
    p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    print(p.stdout, flush=True)
    if p.returncode:
        raise SystemExit(f'preflight failed: {cmd} exit={p.returncode}')

def summarize(result):
    lines = []
    lines.append(f"avg={result.get('avg_score')} success={result.get('success_count')}/{result.get('case_count')}")
    for c in result.get('case_results', []):
        lines.append(f"{c.get('case_file')}: score={c.get('total_score')} assigned={c.get('assigned_count')}/{c.get('total_tasks')} time={c.get('elapsed_ms')} status={c.get('status')}")
    return '\n'.join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--solver', default='solver.py')
    ap.add_argument('--note', default='')
    ap.add_argument('--skip-submit', action='store_true')
    args = ap.parse_args()
    solver = ROOT / args.solver
    code = solver.read_text(encoding='utf-8')
    raw = code.encode('utf-8')
    sha = hashlib.sha256(raw).hexdigest()
    print(f'[candidate] {solver} size={len(raw)} sha256={sha} note={args.note}', flush=True)
    if len(raw) >= 80000:
        raise SystemExit('solver.py too large')
    if 'PROBE_MODE' in code and 'PROBE_MODE = None' not in code:
        raise SystemExit('possible probe mode enabled')
    if not re.search(r'^def\s+solve\s*\(\s*input_text\b', code, re.M):
        raise SystemExit('missing solve(input_text) entry')
    run([sys.executable, '-m', 'py_compile', str(solver)], timeout=30)
    run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py'], timeout=60)
    run([sys.executable, '_bench.py', str(solver), '1'], timeout=40)
    health = request_json('GET', '/health', timeout=15, tries=3)
    print('[health]', json.dumps(health, ensure_ascii=False), flush=True)
    record = {
        'started_at': dt.datetime.now().isoformat(timespec='seconds'),
        'team': TEAM,
        'solver': str(solver),
        'size': len(raw),
        'sha256': sha,
        'note': args.note,
        'health': health,
    }
    if args.skip_submit:
        print('[skip_submit] preflight only')
        return
    resp = request_json('POST', '/judge', {'code': code, 'token': TOKEN}, timeout=60, tries=5)
    record['submit_response'] = resp
    print('[submit_response]', json.dumps(resp, ensure_ascii=False), flush=True)
    if resp.get('error'):
        out = ROOT / 'runs' / f'official_submit_failed_{dt.datetime.now():%Y%m%d_%H%M%S}.json'
        out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        raise SystemExit('submit returned error')
    job = resp['job_id']
    record['job_id'] = job
    result = None
    deadline = time.time() + 420
    poll = 0
    while time.time() < deadline:
        time.sleep(3)
        poll += 1
        r = request_json('GET', f'/result/{job}', timeout=30, tries=5)
        if poll == 1 or poll % 5 == 0 or r.get('status') not in ('queued', 'running'):
            print(f'[poll {poll}]', json.dumps(r, ensure_ascii=False)[:2500], flush=True)
        if r.get('status') not in ('queued', 'running'):
            result = r
            break
    record['finished_at'] = dt.datetime.now().isoformat(timespec='seconds')
    record['result'] = result or {'status': 'timeout'}
    out = ROOT / 'runs' / f'official_submit_{dt.datetime.now():%Y%m%d_%H%M%S}_{sha[:8]}.json'
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print('[saved]', out, flush=True)
    if result:
        print(summarize(result), flush=True)
    else:
        raise SystemExit('result timeout')

if __name__ == '__main__':
    main()
