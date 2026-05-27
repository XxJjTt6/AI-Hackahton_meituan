# High Guard Compression Note

`af88b6fc` only differed from `41db4b34` by ~2.4KB helper/call and still made scarce flip to bad `1589.3393`, likely due timing/code layout. If high guard is ever useful near 700, implement it with minimal inline pattern instead of large lists:

- Check exact current high output contains four old groups and all four replacement rows exist.
- Replace only those four keys in result dict.
- Avoid full 27-row `canon()` lists.

Do not submit now because expected avg gain is only `0.229`, below current threshold.

Compact version prepared: `runs/candidate_high_guard_compact.py`, size `76844`, +736 bytes / 12 inserted lines vs safe best. It should be safer than `af88b6fc`, but expected avg gain only `0.229`; do not submit until near 700.
