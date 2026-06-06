from pathlib import Path
base=Path('solver.py').read_text()
old="if M<J-1e-12:J=M;N=L;D=B,A"
for th in [-0.05,-0.1,-0.2,-0.5]:
    # only accept extra dispatch if marginal improves at least |th|
    new=f"if M<J-1e-12 and M<{th}:J=M;N=L;D=B,A"
    s=base.replace(old,new,1)
    p=Path('runs')/('extra_dispatch_thresh_'+str(abs(th)).replace('.','p')+'.py')
    p.write_text(s); print(p)
