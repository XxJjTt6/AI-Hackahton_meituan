# Big Candidate Backlog

1. Low exact K=2 solver (potentially big)
   - Need: generate top 10-15 pair options per task, solve no-overlap assignment exactly/near-exact within ~1s.
   - Current Python DP too slow; possible approach: branch tasks by fewest feasible options + lower bound + greedy incumbent.
   - Only submit if local hidden-like harness shows stable large improvement and runtime safe.

2. Scarce alternative pairing (potentially medium)
   - Current official-column DP says no improvement from observed rows.
   - Need: generate new pairings that reduce 1531 to <1500 without trying T0033 bad family.

3. Official-column mining (small, postpone)
   - high guard can improve high by 2.29 case points but below current threshold and has hard-case instability risk.
   - Save until score near 700.

4. Objective constants (blacklisted)
   - p80/p70 global not route to 700; official negative.
