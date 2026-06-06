from pathlib import Path
base=Path('solver.py').read_text()
variants={
 'picklow_margin20.py': base.replace('if H<=C+25.:return F','if H<=C+20.:return F'),
 'picklow_margin30.py': base.replace('if H<=C+25.:return F','if H<=C+30.:return F'),
 'hardscarce_penalty55.py': base.replace('return C+60.*(len(I)-len(B))+14.*L+N+M/5.','return C+55.*(len(I)-len(B))+14.*L+N+M/5.'),
 'hardscarce_penalty65.py': base.replace('return C+60.*(len(I)-len(B))+14.*L+N+M/5.','return C+65.*(len(I)-len(B))+14.*L+N+M/5.'),
 'hardscarce_extra16.py': base.replace('return C+60.*(len(I)-len(B))+14.*L+N+M/5.','return C+60.*(len(I)-len(B))+16.*L+N+M/5.'),
}
for n,s in variants.items():
    p=Path('runs')/n; p.write_text(s); print(p)
