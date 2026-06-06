#!/usr/bin/env python3
import json,glob,os
for p in sorted(glob.glob('runs/official_submit_20260518_*.json'))[-12:]:
 try: d=json.load(open(p)); r=d.get('result') or {}
 except: continue
 print(os.path.basename(p), d.get('sha256','')[:8], r.get('avg_score'), 'rem', d.get('submit_response',{}).get('daily_remaining'))
 for c in r.get('case_results',[]):
  if c['case_file']=='scarce_couriers_seed401.txt': print('  scarce',c['total_score'],c['assigned_count'],c['elapsed_ms'])
