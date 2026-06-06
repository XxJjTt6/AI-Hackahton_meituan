import json, importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('s',ROOT/'solver.py'); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
text=(ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt').read_text()
out=s.solve(text)
ours={k:tuple(ls) for k,ls in out}
rs=json.load(open(ROOT/'runs/official_submit_20260520_132026_70222083.json'))['result']['case_results']
off=None
for c in rs:
 if c['case_file']=='large_seed301.txt': off=c
offm={d['task_id_list']:tuple(d['couriers']) for d in off['detail']}
print('ours groups',len(ours),'official groups',len(offm),'official score',off['total_score'])
print('only ours', sorted(set(ours)-set(offm))[:20])
print('only off ', sorted(set(offm)-set(ours))[:20])
chg=[]
for k in sorted(set(ours)&set(offm)):
 if ours[k]!=offm[k]: chg.append((k,ours[k],offm[k]))
print('changed',len(chg))
for x in chg[:80]: print(x)
