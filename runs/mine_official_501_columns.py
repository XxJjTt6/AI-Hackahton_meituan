import json,glob,os
cols={}
for f in glob.glob('runs/official_submit_*.json')+glob.glob('runs/official_result_*.json'):
 try:d=json.load(open(f)); r=d.get('result') or d
 except Exception:continue
 for case in r.get('case_results') or []:
  if case.get('case_file')!='low_willingness_seed501.txt':continue
  for x in case.get('detail') or []:
   ts=tuple(sorted(x['task_id_list'].split(',')));cs=tuple(x['couriers']);cost=float(x['cost']);key=(ts,cs)
   if key not in cols or cost<cols[key][0]:cols[key]=(cost,os.path.basename(f))
T={f'T{i:04d}':i for i in range(30)};C={f'C{i:03d}':i for i in range(60)};items=[]
for (ts,cs),(cost,f) in cols.items():
 if any(t not in T for t in ts) or any(c not in C for c in cs):continue
 sav=100*len(ts)-cost
 if sav<=0:continue
 mask=0
 for t in ts:mask|=1<<T[t]
 for c in cs:mask|=1<<(30+C[c])
 items.append((sav,cost,mask,ts,cs,f))
items.sort(key=lambda x:x[0],reverse=True);n=len(items);conf=[0]*n
for i in range(n):
 for j in range(i+1,n):
  if items[i][2]&items[j][2]:conf[i]|=1<<j;conf[j]|=1<<i
sav=[x[0] for x in items]
from functools import lru_cache
@lru_cache(None)
def ub(av):
 s=0;m=av
 while m:
  b=m&-m;i=b.bit_length()-1;s+=sav[i];m-=b
 return s
best_s=0;best=[];nodes=0
def dfs(av,cur,pick):
 global best_s,best,nodes
 nodes+=1
 if cur+ub(av)<=best_s+1e-9:return
 if cur>best_s:best_s=cur;best=pick[:]
 if not av:return
 m=av;bi=-1;bv=-1
 while m:
  b=m&-m;i=b.bit_length()-1;m-=b;v=sav[i]*(1+(conf[i]&av).bit_count())
  if v>bv:bi=i;bv=v
 dfs(av&~conf[bi]&~(1<<bi),cur+sav[bi],pick+[bi]);dfs(av&~(1<<bi),cur,pick)
dfs((1<<n)-1,0,[])
print('cols',len(cols),'items',n,'nodes',nodes,'best',round(3000-best_s,4),'covered',sum(len(items[i][3]) for i in best),'groups',len(best))
for i in sorted(best,key=lambda i:items[i][3]):print(','.join(items[i][3]),list(items[i][4]),round(items[i][1],4),items[i][5])
