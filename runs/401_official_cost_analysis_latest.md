# 401 Official Cost Analysis

- Official result files/cases scanned: `87`
- Unique known official rows: `57`
- Known row cost conflicts: `0`
- Best current target: `1531.5317`
- Best known-row set-packing score: `1531.5316`
- Best known-row coverage: `39/40`
- Search nodes: `725`

## Decision

Known official rows do **not** contain a safe `>1.0` improvement over the current `1531.5317` hard-cache. The apparent sub-0.001 delta is rounding noise. Do not modify `solver.py` from this result alone.

## Scarce Score Distribution

- `1531.5317`: `53` cases
- `1544.6695`: `1` cases
- `1567.9502`: `2` cases
- `1571.9010`: `1` cases
- `1588.7572`: `7` cases
- `1589.3393`: `21` cases
- `1873.0102`: `1` cases
- `2198.5987`: `1` cases

## Best Known-Row Packing

- Missing tasks: `T0033`
- Selected rows: `20`
- `T0000,T0027` -> `C005` cost `72.2550`
- `T0001,T0035` -> `C018` cost `107.8965`
- `T0002,T0038` -> `C009` cost `58.9084`
- `T0003,T0024` -> `C012` cost `67.0227`
- `T0004,T0018` -> `C007` cost `66.6087`
- `T0005,T0036` -> `C019` cost `82.7552`
- `T0006,T0030` -> `C003` cost `64.6652`
- `T0007,T0008` -> `C001` cost `89.3427`
- `T0009,T0011` -> `C014` cost `67.6793`
- `T0010,T0029` -> `C004` cost `94.8247`
- `T0012,T0019` -> `C010` cost `93.9187`
- `T0013,T0039` -> `C013` cost `62.6715`
- `T0014,T0031` -> `C008` cost `69.0409`
- `T0015,T0034` -> `C015` cost `72.9971`
- `T0016` -> `C000` cost `30.1665`
- `T0017,T0032` -> `C002` cost `62.4523`
- `T0020,T0023` -> `C016` cost `89.2482`
- `T0021,T0026` -> `C017` cost `48.6049`
- `T0022,T0037` -> `C011` cost `59.4672`
- `T0025,T0028` -> `C006` cost `71.0059`

## Known T0033 Rows

- `T0033` -> `C000` cost `83.1439` from `official_submit_20260520_152714_0fc08e17.json` total `1571.9010`
- `T0019,T0033` -> `C010` cost `118.3442` from `official_submit_20260517_235832_bce9292a.json` total `1873.0102`

## Forced T0033 Known-Row Optima

- Force `T0033` -> `C000` cost `83.1439` => best known score `1571.9011`, delta `+40.3694`, coverage `39/40`, nodes `635`
  - Additional non-baseline rows: `T0016,T0020` -> `C016` cost `91.2256`; `T0023,T0025` -> `C006` cost `56.4206`
- Force `T0019,T0033` -> `C010` cost `118.3442` => best known score `1555.9571`, delta `+24.4254`, coverage `39/40`, nodes `1478`

## Best Near-Miss Upgrade Thresholds

- Closest worse observed scarce structure: `1544.6695` from `official_submit_20260519_171835_ac55cf9c.json`, gap `+13.1378`
- Missing tasks in that structure: `T0028, T0033`
- Since all 20 scarce couriers are used, the most plausible safe improvement is replacing a selected single-task row by a same-courier two-task bundle containing one missing task.
- Replace `T0001` -> `C018` cost `38.4593` with `T0001,T0033` -> same couriers; official cost must be `< 125.3215` to beat current, `< 124.3215` to justify a submit.
- Replace `T0001` -> `C018` cost `38.4593` with `T0001,T0028` -> same couriers; official cost must be `< 125.3215` to beat current, `< 124.3215` to justify a submit.
- Replace `T0016` -> `C000` cost `30.1665` with `T0016,T0033` -> same couriers; official cost must be `< 117.0287` to beat current, `< 116.0287` to justify a submit.
- Replace `T0016` -> `C000` cost `30.1665` with `T0016,T0028` -> same couriers; official cost must be `< 117.0287` to beat current, `< 116.0287` to justify a submit.

## Most Common 401 Structures

- Structure `1`: count `53`, rows `20`, coverage `39/40`, missing `T0033`
- Structure `2`: count `21`, rows `19`, coverage `38/40`, missing `T0028, T0033`
- Structure `3`: count `7`, rows `19`, coverage `38/40`, missing `T0028, T0033`
- Structure `4`: count `2`, rows `19`, coverage `38/40`, missing `T0028, T0033`
- Structure `5`: count `1`, rows `20`, coverage `40/40`, missing `none`
- Structure `6`: count `1`, rows `18`, coverage `25/40`, missing `T0004, T0005, T0007, T0008, T0009, T0010, T0015, T0017, T0019, T0020, T0024, T0027, T0028, T0029, T0033`
- Structure `7`: count `1`, rows `20`, coverage `38/40`, missing `T0028, T0033`
- Structure `8`: count `1`, rows `20`, coverage `39/40`, missing `T0028`

## Cost Conflicts

- No duplicate official row has conflicting rounded cost.

## Next Probe Candidates

Probe only if it guarantees visible detail for the target row and cannot collapse into the known `1589.3393` family.
- Highest-value missing information remains alternative official costs for rows containing `T0033`.
- A useful probe should force exactly one candidate `T0033` row while preserving enough of the hard-cache to keep the detail interpretable.
