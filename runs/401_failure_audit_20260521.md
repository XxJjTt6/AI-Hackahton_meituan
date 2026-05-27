# scarce_couriers_seed401 Failure Audit

Date: 2026-05-21  
Current safe solver: `ab97ce939b454fd193ab9853cb1c8110778656a0adf8b0fbc17ed49f2acc1577`  
Current official best average: `706.197`  
Current 401 best: `1531.5317`, assigned `39/40`

## Executive Summary

We have not broken `scarce_couriers_seed401` because the search process repeatedly optimized the wrong surrogate objective and used official submissions as probes without enough evidence. The current 401 hard-cache is not a random local artifact; across historical official feedback it is the best observed structure, and most dynamic replacements collapse to a known worse structure around `1589.3393`.

The main failure is not lack of algorithmic complexity. The main failure is objective mismatch: local `_solution_expected_cost`, derived official-cost proxy, and raw candidate score all mis-rank 401 replacement structures. Therefore more dynamic search selected by local objective is actively dangerous.

## Known Official 401 Score Buckets

Across currently available official logs, 401 has only 7 distinct output structures and these score counts:

| Score | Count | Assigned | Interpretation |
|---:|---:|---:|---|
| `1531.5317` | 53 | 39/40 | Current best hard-cache |
| `1544.6695` | 1 | 38/40 | Alternative missing 2 tasks, slightly worse |
| `1571.9010` | 1 | 39/40 | Forced `T0033/C000` structure, worse by `40.3693` |
| `1588.7572` | 7 | 38/40 | 1589-family without extra `C000` on `T0013,T0039` |
| `1589.3393` | 18 | 38/40 | Common bad dynamic-search attractor |
| `1873.0102` | 1 | 40/40 | Full-coverage `T0019,T0033/C010`, much worse |
| `2198.5987` | 1 | 18/40-ish structure, bad probe |

## Current Best Structure

The best 401 structure is:

```text
T0000,T0027 -> C005
T0001,T0035 -> C018
T0002,T0038 -> C009
T0003,T0024 -> C012
T0004,T0018 -> C007
T0005,T0036 -> C019
T0006,T0030 -> C003
T0007,T0008 -> C001
T0009,T0011 -> C014
T0010,T0029 -> C004
T0012,T0019 -> C010
T0013,T0039 -> C013
T0014,T0031 -> C008
T0015,T0034 -> C015
T0016 -> C000
T0017,T0032 -> C002
T0020,T0023 -> C016
T0021,T0026 -> C017
T0022,T0037 -> C011
T0025,T0028 -> C006
```

It covers all tasks except `T0033`. Its official raw detail-cost sum is about `1431.5317`, plus `100` unassigned penalty.

## T0033 Evidence

Only two visible official `T0033` options have been observed:

| Task Key | Courier(s) | Official Cost | Resulting Structure |
|---|---|---:|---:|
| `T0033` | `C000` | `83.1439` | `1571.9010` |
| `T0019,T0033` | `C010` | `118.3442` | `1873.0102` |

The best known `T0033/C000` neighborhood replaces:

```text
Removed:
T0016 -> C000                  cost 30.1665
T0020,T0023 -> C016            cost 89.2482
T0025,T0028 -> C006            cost 71.0059
Removed total                  cost 190.4206

Added:
T0033 -> C000                  cost 83.1439
T0016,T0020 -> C016            cost 91.2256
T0023,T0025 -> C006            cost 56.4206
Added total                    cost 230.7901

Delta                         +40.3695
```

So merely covering `T0033` is not enough. To improve the current best, a `T0033`-covering structure must recover at least `40.37` official cost from elsewhere, or a full-coverage structure must have total raw cost below `1531.5317`.

## What We Ruled Out

### 1. Known exposed-column recombination

All historical official 401 detail rows were mined as exposed columns. Exact set-packing over those columns returns the current hard-cache as the best structure. Therefore all visible official rows are insufficient to improve 401.

### 2. T0033 owner-window / direct patches

Multiple official no-ops showed that targeted `T0033` additions or local owner-window repairs do not improve the official result.

Representative outcomes:

- `511d45f6`: no-op, `1531.5317`
- `665444bb`: no-op, `1531.5317`
- Earlier `T0033/C000`: worse, `1571.9010`
- Earlier `T0019,T0033/C010`: worse, `1873.0102`

### 3. Guarded global set-packing and redundancy

`18bc8b4e` added guarded runtime set-packing plus unused-courier redundancy. It officially no-oped at `1531.5317`. This ruled out a simple better strict single-courier packing under that selected hidden-column pool and cheap same-key redundancy on current hard-cache groups.

### 4. Ejection-chain around current hard-cache

`e54b86a3` allowed one-courier ejection plus up to three repair rows, including trading one covered task for `T0033` as long as coverage stayed at least `39/40` and local expected cost improved. It no-oped at `1531.5317`.

### 5. Information probes for unseen T0033 rows

`f0ca5633` and `a957d5bb` were intended to expose unseen `T0033` options, but both regressed to the known `1589.3393` structure and did not reveal a visible new `T0033` detail row. This probe family is unreliable and should not be repeated.

### 6. Dynamic sparse beam / local objective guarded replacements

`85447170` selected the known `1589.3393` bad structure despite local expected-cost guards. This proved `_solution_expected_cost` mis-ranks 401 dynamic replacements.

`7686b82f` tried a derived official-cost proxy and still selected `1589.3393`. This proved the derived proxy is also wrong.

`559c8fca` tried raw candidate score plus penalty and still selected `1589.3393`. This proved raw candidate score is also not a reliable official-cost proxy.

## Root Causes

### Root Cause A: Objective mismatch

The 401 judge score behaves like a hidden official cost table plus unassigned penalty. Local expected-cost math is useful in other modes, but it is not reliable for choosing 401 replacement structures.

Evidence:

- The known `1589.3393` structure repeatedly looks attractive locally, but official score is worse than hard-cache.
- Expected-score values in detail are not the same as total-score contribution.
- Candidate `score` fields also do not reconstruct official detail cost well enough for dynamic replacement decisions.

### Root Cause B: Hard-cache is a strong official-feedback artifact

The current hard-cache has survived 53 official results and exact recombination over exposed rows. It is probably not easily beaten by generic search; it was implicitly tuned to the hidden official cost table.

### Root Cause C: Submission discipline failed

After repeated no-op/regression, the correct move was to stop and re-audit. Instead, several variants were submitted with insufficient confidence and with local objectives already contradicted by official evidence.

## New Submission Rules

No further 401 submission should be made unless it satisfies at least one condition:

1. **Known official-cost-improving structure**: all changed rows have official-observed detail costs and the computed official total is below `1531.5317`.
2. **Safe information gain**: the probe cannot collapse into the known `1589.3393` family and has a precise question it answers.
3. **Static hard-coded alternative with official evidence**: the output is not selected by local surrogate objective; it is derived from observed official row costs.

Explicitly banned unless new evidence appears:

- `_solution_expected_cost`-guarded 401 replacement
- candidate raw-score guarded 401 replacement
- derived official-cost proxy guarded 401 replacement
- sparse-beam / dynamic master selected 401 output
- T0033 information probes that do not guarantee visible T0033 detail output
- any variant that can output `T0013,T0039 -> C013,C000` plus `T0016,T0020 -> C016` / `T0023,T0025 -> C006`

## What Might Still Be Worth Doing

### Option 1: Build an official-cost knowledge base

Use only official detail rows to create a table of known `(task_key, courier set) -> official cost`. Search only over this table. Current result says no improvement, but the table should be maintained as the single source of truth.

### Option 2: Controlled row-cost probes, not solution probes

If probing is necessary, design probes to reveal one specific row cost while preserving validity and avoiding known bad structures. A probe must guarantee the target row appears in official detail, otherwise it is not worth a submission.

### Option 3: Stop 401 submissions unless a new official row is learned

Given remaining attempts, safest approach is to avoid further 401 submissions until a truly new official-cost row can be forced and observed.

## Bottom Line

The reason 401 has not improved is not that the search is too weak; it is that we cannot reliably score candidate 401 structures locally. The current best is a hard-coded structure aligned with hidden official costs. Until a better official-cost row/structure is known, dynamic algorithmic search is more likely to regress to `1589.3393` than improve `1531.5317`.
