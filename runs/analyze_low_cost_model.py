#!/usr/bin/env python3
import sys, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
import solver
pairs=[('T0000',['C017','C051'],60.7403),('T0001',['C021','C019'],61.8923),('T0002',['C015','C016'],61.7599),('T0003',['C025','C000'],60.463),('T0004',['C033','C001'],62.798),('T0005',['C043','C023'],57.8097),('T0006',['C034','C038'],61.7497),('T0007',['C002','C026'],59.5019),('T0008',['C013','C041'],56.4021),('T0009',['C024','C059'],61.7274),('T0010',['C047','C027'],60.2994),('T0011',['C057','C039'],58.2661),('T0012',['C042','C005'],62.5017),('T0013',['C029','C056'],61.0391),('T0014',['C044','C032'],58.878),('T0015',['C040','C045'],59.4528),('T0016',['C011','C008'],62.3386),('T0017',['C004','C046'],58.2459),('T0018',['C036','C022'],57.944),('T0019',['C007','C020'],57.1355),('T0020',['C053','C009'],61.1896),('T0021',['C058','C014'],59.0679),('T0022',['C049','C048'],59.2874),('T0023',['C010','C050'],57.0239),('T0024',['C006','C055'],58.8237),('T0025',['C003','C037'],54.7695),('T0026',['C052','C031'],60.6674),('T0027',['C018','C054'],62.6548),('T0028',['C030','C035'],62.1352),('T0029',['C028','C012'],63.3383)]
for scale in [.2,.25,.3,.35,.4,.5]:
    rows,tasks,c=proxy_eval.parse(proxy_eval.make_low(scale)); row={(r[0],r[2]):r for r in rows}
    vals=[]; miss=0
    for k,cs,off in pairs:
        if all((k,c) in row for c in cs):
            rs=[row[(k,c)] for c in cs]; vals.append((solver._group_expected_cost(rs,1), off))
        else: miss+=1
    if vals:
        ratios=[off/local for local,off in vals]
        print('scale',scale,'local_sum',sum(x for x,_ in vals),'off_sum',sum(y for _,y in vals),'ratio_mean',sum(ratios)/len(ratios),'ratio_minmax',(min(ratios),max(ratios)))
