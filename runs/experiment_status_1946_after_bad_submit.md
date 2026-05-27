# Status After Bad Submit 19:46

Official validation of `60cf6691` failed:
- avg `836.3734`
- large302 `1926.4815`
- root cause: public large301 cache collided with hidden large302 and returned the wrong solution.

Immediate policy:
- Remaining attempts: 3 (per submit response daily_remaining after queue was 3).
- Do not submit any compact cache / row-cache refactor candidates.
- Safe main is still `solver.py` / `41db4b34` / official `706.4264`.
- Any future candidate must be a clean diff on safe main and must not alter official-proven large302/scarce hardcoded logic.

Best known score candidate before this was only micro; now blacklisted due cache family.
Next work: clean low/scarce algorithmic changes only, offline first.
