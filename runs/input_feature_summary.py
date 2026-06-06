#!/usr/bin/env python3
import sys, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
for name,text in [('large301',proxy_eval.DATA.read_text()),('low020',proxy_eval.make_low(.20)),('low025',proxy_eval.make_low(.25)),('low030',proxy_eval.make_low(.30)),('scarce40',proxy_eval.make_scarce())]:
    rows,tasks,couriers=proxy_eval.parse(text)
    w=[r[4] for r in rows]; sc=[r[3] for r in rows]; single=[r for r in rows if len(r[1])==1]
    ws=[r[4] for r in single]
    print(name, {'rows':len(rows),'tasks':len(tasks),'couriers':len(couriers),'avg_w':round(sum(w)/len(w),6),'avg_single_w':round(sum(ws)/len(ws),6),'minmax_w':(round(min(w),4),round(max(w),4)),'avg_score':round(sum(sc)/len(sc),4),'bundle_frac':round(sum(1 for r in rows if len(r[1])>1)/len(rows),4)})
