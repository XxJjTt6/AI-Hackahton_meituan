from pathlib import Path
base=Path('solver.py').read_text()
repls={
 'single_sort_w_first.py': ("E=sorted(E,key=lambda c:(c[3],-c[4],c[5]));O.append((A,[A[2]for A in E]))", "E=sorted(E,key=lambda c:(-c[4],c[3],c[5]));O.append((A,[A[2]for A in E]))"),
 'format_w_first.py': ("D=sorted(A[C],key=lambda c:(c[3],-c[4],c[5]));B.append((C,[A[2]for A in D]))", "D=sorted(A[C],key=lambda c:(-c[4],c[3],c[5]));B.append((C,[A[2]for A in D]))"),
}
for name,(old,new) in repls.items():
    s=base.replace(old,new)
    p=Path('runs')/name; p.write_text(s); print(p)
