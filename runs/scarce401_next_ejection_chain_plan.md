# scarce401 next idea: redundancy ejection-chain

Official no-op 18bc8b4e ruled out:
- better single-courier set packing under implemented top-column filter
- direct unused-courier same-key redundancy on current hard-cache groups

Remaining plausible move class:
1. Add a currently-used courier c_j as second rider to another expensive/risky bundle g_i if group expected cost drops a lot.
2. Repair c_j original group by either:
   - replacing it with an unused courier on same task_key, or
   - opening one/two alternate bundles covering the released tasks using unused couriers.
3. Accept only if exact `_solution_expected_cost` improves and coverage does not decrease.

This is a real ejection-chain: it can discover moves like historical C000 joining T0013,T0039 only if T0016 can be cheaply repaired. Direct redundancy and T0033-only probes could not test this full chain.
