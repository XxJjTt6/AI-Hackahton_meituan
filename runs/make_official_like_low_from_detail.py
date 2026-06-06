#!/usr/bin/env python3
# Create synthetic input where known official low K=2 pairs have costs closer to official by boosting willingness.
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runs'))
import proxy_eval
pairs={
'T0000':{'C017','C051'},'T0001':{'C021','C019'},'T0002':{'C015','C016'},'T0003':{'C025','C000'},'T0004':{'C033','C001'},'T0005':{'C043','C023'},'T0006':{'C034','C038'},'T0007':{'C002','C026'},'T0008':{'C013','C041'},'T0009':{'C024','C059'},'T0010':{'C047','C027'},'T0011':{'C057','C039'},'T0012':{'C042','C005'},'T0013':{'C029','C056'},'T0014':{'C044','C032'},'T0015':{'C040','C045'},'T0016':{'C011','C008'},'T0017':{'C004','C046'},'T0018':{'C036','C022'},'T0019':{'C007','C020'},'T0020':{'C053','C009'},'T0021':{'C058','C014'},'T0022':{'C049','C048'},'T0023':{'C010','C050'},'T0024':{'C006','C055'},'T0025':{'C003','C037'},'T0026':{'C052','C031'},'T0027':{'C018','C054'},'T0028':{'C030','C035'},'T0029':{'C028','C012'}}
rows,tasks,couriers=proxy_eval.parse(proxy_eval.make_low(.25))
out=[]
for k,ts,c,sc,w,i in rows:
    if len(ts)==1 and c in pairs.get(ts[0],set()):
        w=min(.95,w*2.2+.08)
    else:
        w=min(.95,w*1.25)
    out.append((k,ts,c,sc,w,i))
print(proxy_eval.serialize(out), end='')
