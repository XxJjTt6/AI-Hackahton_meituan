# concise current opportunities from all official details, using safe best as baseline
import subprocess,sys,re
out=subprocess.check_output([sys.executable,'runs/official_column_beam_all.py'], text=True, timeout=60)
for line in out.splitlines():
    if line.startswith('[baseline') or line.startswith('CASE'):
        print(line)
