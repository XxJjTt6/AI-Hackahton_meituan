from pathlib import Path
base=Path('solver.py').read_text()
# Change selection ordering only, not cost evaluator, so cross-score remains meaningful.
repls={
 'rank_more_w.py': ("return F,A/max(1,H),G,A/max(B,1e-09),A,-len(E)", "return F,G,A/max(1,H),A/max(B,1e-09),A,-len(E)"),
 'rank_ratio_first.py': ("return F,A/max(1,H),G,A/max(B,1e-09),A,-len(E)", "return A/max(B,1e-09),F,A/max(1,H),G,A,-len(E)"),
 'sparse_gain_first.py': ("if mode==_G:E=D,A/max(C,1e-09),A,I,-C", "if mode==_G:E=A,D,A/max(C,1e-09),I,-C"),
}
for name,(old,new) in repls.items():
    s=base.replace(old,new,1)
    p=Path('runs')/name; p.write_text(s); print(p)
