#!/usr/bin/env python3
import json, os, collections
safe='runs/official_submit_20260519_171310_41db4b34.json'
bad='runs/official_submit_20260519_193824_60cf6691.json'
def load(p):
    r=json.load(open(p))['result']['case_results']; return {c['case_file']:(c['total_score'],c['elapsed_ms'],c['assigned_count'],c.get('unassigned_count')) for c in r}
S=load(safe); B=load(bad)
print('Safe total',sum(v[0] for v in S.values()),'avg',sum(v[0] for v in S.values())/10)
print('Need total reduction to avg700',sum(v[0] for v in S.values())-7000)
print('\ncase safe_score time_ms bad_delta_to_60cf')
for k,v in sorted(S.items(), key=lambda kv: kv[1][0], reverse=True):
    bd=B.get(k,(None,))[0]
    delta=None if bd is None else bd-v[0]
    print(f'{k:30s} {v[0]:9.4f} {v[1]:5d} delta_bad={delta}')
print('\nIf one case improves alone, required target score:')
need=sum(v[0] for v in S.values())-7000
for k,v in sorted(S.items(), key=lambda kv: kv[1][0], reverse=True):
    print(f'{k:30s} must go from {v[0]:.4f} to {v[0]-need:.4f} ({need:.2f} gain)')
