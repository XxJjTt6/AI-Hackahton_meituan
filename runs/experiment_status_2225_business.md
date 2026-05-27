# Business Iteration Status 22:25

Remaining official attempts: 2.

Official failure just before this:
- `52daa29b` avg `712.2072`; high did not improve; scarce regressed to `1589.3393`. Blacklisted.

Business/portfolio candidates:
- `candidate_business_time_sla.py`: global deadline 8.45/8.65; low calibrated same sig and faster; public large stable in audit; no score-gain evidence.
- `candidate_sla_scarce_pick1081.py`: SLA + scarce picker expected-cost-first; low same sig, public large 3/3 best sig in audit, scarce proxy sometimes improves `1097 -> 1081`; official seed401 hard-cache means likely no official score gain.
- `candidate_sla_scarce_highfull.py`: rejected; severe public large bad sig `682.189827`.
- `candidate_business_low_probability.py`: rejected; low proxy worsened.

Current best structural candidate (not submit-worthy by score threshold):
- `runs/candidate_sla_scarce_pick1081.py`, SHA `51aa074b`, size `76109`.
- It is a stability/business-SLA candidate, not a proven leaderboard-improver.

Decision:
- Do not submit unless user explicitly chooses a structural stability gamble.
- Continue looking for direct low/scarce official-score evidence.
