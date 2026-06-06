import importlib.util, pathlib, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
CASES=[ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt',ROOT/'runs/synth_medium_from_large301_30x60.txt',ROOT/'runs/official_like_low_synth.txt']
def load():
 spec=importlib.util.spec_from_file_location('s',ROOT/'solver.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def parse(text):
 lines=text.strip().splitlines(); st=1 if lines and lines[0].startswith('task') else 0; C=[];B=set()
 for idx,l in enumerate(lines[st:]):
  a=l.split('\t')
  if len(a)<4:continue
  k,c,sc,w=a[:4]; ts=tuple(x.strip() for x in k.split(',') if x.strip()); C.append((k,ts,c,float(sc),float(w),idx)); B.update(ts)
 return C,B
for mode in ['baseline','min_score','max_willingness']:
 s=load()
 if mode!='baseline':
  orig=s._group_expected_cost
  def gc(rows,task_count,extra=None,mode=mode):
   if extra is not None: rows=list(rows)+[extra]
   return s._group_expected_cost_by_model(rows,task_count,mode)
  s._group_expected_cost=gc
 print('MODE',mode)
 for p in CASES:
  text=p.read_text(); C,B=parse(text); t=time.monotonic(); out=s.solve(text); dt=time.monotonic()-t
  # evaluate all three models using fresh baseline module to avoid monkey patch recursion
  ev=load(); sig=tuple(sorted((k,tuple(sorted(ls))) for k,ls in out))
  vals={m:ev._solution_expected_cost_by_model(out,C,B,m) for m in ['avg_subset','min_score','max_willingness']}
  cov=set(); row={(r[0],r[2]):r for r in C}
  for k,ls in out:
   rr=row.get((k,ls[0])) if ls else None
   if rr: cov.update(rr[1])
  print(p.name, 'time',round(dt,2),'groups',len(out),'cov',len(cov),'vals', {k:round(v,2) for k,v in vals.items()}, 'sighash',hash(sig))
