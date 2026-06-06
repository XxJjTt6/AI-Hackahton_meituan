#!/usr/bin/env python3
from __future__ import annotations
import glob,json,os

BEST='runs/official_submit_20260520_132026_70222083.json'
TARGETS=['high_noise_seed601.txt','medium_seed201.txt','medium_seed202.txt','medium_seed203.txt','large_seed302.txt','small_seed100.txt','tiny_seed42.txt']

def load(path):
    d=json.load(open(path)); r=d.get('result') or {}
    return d,r,{c['case_file']:c for c in r.get('case_results',[])}

def sig(case):
    return tuple(sorted((g['task_id_list'],tuple(g['couriers'])) for g in case.get('detail',[])))

def struct(case):
    from collections import Counter
    return Counter((len(g['task_id_list'].split(',')),len(g['couriers'])) for g in case.get('detail',[]))

def main():
    bd,br,bc=load(BEST)
    for target in TARGETS:
        base=bc[target]
        print('\nCASE',target,'best',base['total_score'],'struct',dict(struct(base)))
        variants=[]
        for p in glob.glob('runs/official_submit_*.json'):
            try:
                d,r,cases=load(p)
                if target not in cases: continue
                c=cases[target]
                delta=round(c['total_score']-base['total_score'],4)
                if delta==0: continue
                variants.append((abs(delta),delta,c['total_score'],os.path.basename(p),d.get('sha256','')[:8],d.get('note','')[:80],dict(struct(c)),sig(c)==sig(base)))
            except Exception: pass
        variants.sort()
        for row in variants[:12]:
            print(' delta',row[1],'score',row[2],row[4],row[3],'same_sig',row[7],'struct',row[6],'note',row[5])
if __name__=='__main__': main()
