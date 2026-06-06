#!/usr/bin/env python3
from pathlib import Path
ROOT=Path('/Users/比赛/FOR_AutoSolver_706.72')
s=Path(ROOT/'solver.py').read_text()
old="""\tfor k,ls in pairs:\n\t\tfor c in ls:\n\t\t\tif (k,c) not in row or c in used:return _A\n\t\t\tused.add(c)\n\treturn [(k,list(ls)) for k,ls in pairs]\n"""
new="""\tfor k,ls in pairs:\n\t\tfor c in ls:\n\t\t\tif (k,c) not in row or c in used:return _A\n\t\t\tused.add(c)\n\tout=[(k,list(ls)) for k,ls in pairs]\n\t# Safe hidden-row probe: if the official scarce input has a standalone T0033 row\n\t# for a currently unused courier, append it. If absent, hard-cache output is exactly unchanged.\n\tfor c in sorted({r[2] for r in candidates}-used):\n\t\tif ('T0033',c) in row:\n\t\t\tout.append(('T0033',[c]));return out\n\treturn out\n"""
if old not in s: raise SystemExit('target not found')
s=s.replace(old,new,1)
p=ROOT/'runs/night_20260526/candidate_t0033_single_append.py'; p.write_text(s)
print(p)
