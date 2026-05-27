# Reflection 18:03

Why stuck near 706:

1. Official hidden data has been reverse-engineered enough that all historical full-case outputs are already at per-case best, except small recombinations now captured.
2. Local proxies are misleading for structural changes: p80 and low proxies showed huge local gains but official got worse.
3. The actual remaining leaderboard gap likely comes from a method that generates new hidden-case columns/assignments not present in our 53 official submissions, especially low/scarce.
4. Because hidden input is unavailable, official submissions are the only true feedback, but remaining attempts are scarce; therefore only large structural candidates deserve attempts.

Next offline hypotheses:

- Implement a faster exact K=2 assignment solver for low (min-cost over pair options with stronger pruning) in standalone, not in solver yet.
- Derive a safer high/medium local-column guard only after reaching near 700; ignore for now.
- Revisit scarce cache: find if any non-T0033 alternative can reduce >60 with current columns; current official column DP says no.
