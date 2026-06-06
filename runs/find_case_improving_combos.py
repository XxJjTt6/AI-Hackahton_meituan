# Summarize all-column narrow beam opportunities and classify submit-worthy deltas.
import subprocess,re,sys
out=subprocess.check_output([sys.executable,'runs/official_column_beam_all.py'], text=True, timeout=50)
print(out)
print('\nSubmit-worthy (>0.01 avg => case delta<-0.1):')
for line in out.splitlines():
    if line.startswith('CASE'):
        m=re.search(r'CASE (\S+) cur ([0-9.]+) beam ([0-9.]+) delta ([\-0-9.]+)', line)
        if m and float(m.group(4)) < -0.1:
            print(line, 'avg_delta', round(float(m.group(4))/10,4))
