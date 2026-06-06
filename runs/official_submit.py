#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path('/Users/比赛/FOR_AutoSolver_706.72')
BASE = 'https://hackathon.mykeeta.com'
TOKEN = '13900139080'
TEAM = '料事如神'
SOLVER = ROOT / 'solver.py'
LOG = ROOT / 'runs' / f'official_submit_{dt.datetime.now():%Y%m%d_%H%M%S}.json'

def post(path, payload, timeout=60):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(BASE + path, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))

def get(path, timeout=60):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))

code = SOLVER.read_text(encoding='utf-8')
sha = hashlib.sha256(code.encode('utf-8')).hexdigest()
started = dt.datetime.now().isoformat(timespec='seconds')
record = {'started_at': started, 'team': TEAM, 'solver': str(SOLVER), 'size': len(code.encode('utf-8')), 'sha256': sha}
print(f"submit solver size={record['size']} sha256={sha}", flush=True)
resp = post('/judge', {'code': code, 'token': TOKEN})
record['submit_response'] = resp
print('submit_response', json.dumps(resp, ensure_ascii=False), flush=True)
if resp.get('error'):
    LOG.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    sys.exit(2)
job = resp.get('job_id')
record['job_id'] = job
result = None
for i in range(1, 421):
    time.sleep(1)
    r = get(f'/result/{job}')
    if i == 1 or i % 10 == 0 or r.get('status') not in ('queued', 'running'):
        print(f"poll {i}s", json.dumps(r, ensure_ascii=False)[:2000], flush=True)
    if r.get('status') not in ('queued', 'running'):
        result = r
        break
record['finished_at'] = dt.datetime.now().isoformat(timespec='seconds')
record['result'] = result or {'status': 'timeout'}
LOG.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print('log', LOG, flush=True)
if result is None:
    sys.exit(3)
print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
