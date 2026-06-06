#!/usr/bin/env python3
import importlib.util,pathlib,time,itertools,sys,argparse
ROOT=pathlib.Path.cwd(); spec=importlib.util.spec_from_file_location('s',ROOT/'solver.py'); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse(text):
 lines=text.strip().splitlines(); off=1 if lines and lines[0].startswith('task') else 0; C=[];B=set()
 for idx,line in enumerate(lines[off:]):
  p=line.split('\t')
  if len(p)<4: continue
  tk,c,cost,prob=p[:4]; tasks=tuple(x for x in tk.split(',') if x)
  C.append((tk,tasks,c,float(cost),float(prob),idx)); B.update(tasks)
 return C,B

def regret_construct(C,B,top=12,kmax=3):
 # choose hardest task by gap between best and kth feasible column, then commit best feasible.
 rows=s._canonical_candidates(C); remaining=set(B); used=set(); out=[]
 bytask={t:[] for t in B}
 for r in rows:
  if len(r[1])==1 and r[1][0] in bytask: bytask[r[1][0]].append(r)
 for t in bytask: bytask[t].sort(key=lambda r:s._single_expected_cost(r))
 while remaining:
  best_choice=None
  for t in list(remaining):
   opts=[]
   cand=[r for r in bytask.get(t,[]) if r[2] not in used][:top]
   for m in range(1,min(kmax,len(cand))+1):
    for comb in itertools.combinations(cand,m):
     if len({r[2] for r in comb})<len(comb): continue
     opts.append((s._group_expected_cost(comb,1),comb))
   opts.sort(key=lambda x:x[0])
   if not opts: continue
   gap=(opts[min(2,len(opts)-1)][0]-opts[0][0]) if len(opts)>1 else 1000
   key=(gap, opts[0][0], -len(opts))
   if best_choice is None or key>best_choice[0]: best_choice=(key,t,opts[0])
  if best_choice is None: break
  _,t,(cost,comb)=best_choice
  out.append((t,[r[2] for r in comb])); used.update(r[2] for r in comb); remaining.remove(t)
 return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('input'); args=ap.parse_args(); text=open(args.input).read(); C,B=parse(text)
 base=s.solve(text); basecost=s._solution_expected_cost(base,C,B); print('base',basecost,len(base))
 for top in [8,12,16,24]:
  for k in [2,3,4]:
   r=regret_construct(C,B,top,k); cost=s._solution_expected_cost(r,C,B); print('regret',top,k,cost,cost-basecost,len(r))
if __name__=='__main__': main()
