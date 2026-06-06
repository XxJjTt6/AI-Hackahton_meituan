import importlib.util, itertools, time, pathlib, json
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('s',ROOT/'solver.py'); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
def parse(text):
 lines=text.strip().splitlines(); st=1 if lines and lines[0].startswith('task') else 0; C=[];B=set()
 for idx,l in enumerate(lines[st:]):
  a=l.split('\t')
  if len(a)<4: continue
  k,c,sc,w=a[:4]; ts=tuple(x.strip() for x in k.split(',') if x.strip()); C.append((k,ts,c,float(sc),float(w),idx)); B.update(ts)
 return C,B
def solve_cols(C,B,deadline,top=14,maxk=4,per_task=80,beam=20000):
 tasks=sorted(B); ci={c:i for i,c in enumerate(sorted({r[2] for r in C}))}; cols=[]
 by={t:[] for t in tasks}
 for r in C:
  if len(r[1])==1: by[r[1][0]].append(r)
 for ti,t in enumerate(tasks):
  rs=sorted(by[t],key=lambda r:s._single_expected_cost(r))[:top]
  local=[]
  for k in range(1,min(maxk,len(rs))+1):
   for comb in itertools.combinations(rs,k):
    cm=0
    for r in comb: cm|=1<<ci[r[2]]
    cost=s._group_expected_cost(list(comb),1)
    local.append((cost,ti,cm,tuple(comb)))
  local=sorted(local,key=lambda x:x[0])[:per_task]
  cols.extend(local)
 states={(0,0):(0.0,())}
 for ti,t in enumerate(tasks):
  if time.monotonic()>deadline-.05: break
  opts=[x for x in cols if x[1]==ti]
  new={}
  for (mask,cmask),(cost,path) in states.items():
   # skip task penalty option
   key=(mask|1<<ti,cmask); val=(cost+100,path)
   if key not in new or val[0]<new[key][0]: new[key]=val
   for co,_,cc,comb in opts:
    if cmask&cc: continue
    key=(mask|1<<ti,cmask|cc); val=(cost+co,path+(comb,))
    if key not in new or val[0]<new[key][0]: new[key]=val
  states=dict(sorted(new.items(),key=lambda kv:kv[1][0])[:beam])
 best=min(states.values(),key=lambda x:x[0])
 out=[]
 for comb in best[1]:
  rows=sorted(comb,key=lambda r:(r[3],-r[4],r[5])); out.append((rows[0][0],[r[2] for r in rows]))
 return out
CASES=[ROOT/'Fwd_ 【美团AI Hackathon大赛】-【命题四AutoSolver：让AI Agent 自主求解配送分配问题】脱敏数据/large_seed301.txt',ROOT/'runs/synth_medium_from_large301_30x60.txt',ROOT/'runs/official_like_low_synth.txt',ROOT/'runs/official_calibrated_low_synth.txt']
for p in CASES:
 text=p.read_text(); C,B=parse(text); base=s.solve(text); bc=s._solution_expected_cost(base,C,B)
 for prm in [(8,3,20,1200),(10,3,25,2200)]:
  t=time.monotonic(); out=solve_cols(C,B,time.monotonic()+3,*prm); cc=s._solution_expected_cost(out,C,B)
  print(json.dumps({'case':p.name,'base':bc,'params':prm,'cost':cc,'delta':cc-bc,'groups':len(out),'time':time.monotonic()-t},ensure_ascii=False))
