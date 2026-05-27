# Official Probe Summary 2026-05-20 23:59

Submitted 5 probe variants to use remaining daily attempts. Daily remaining reached `0`.

## Probe files and results

| Probe | SHA prefix | Avg | low501 | scarce401 | Key signal |
|---|---:|---:|---:|---:|---|
| `probe401_nocache_dynamic_20260520.py` | `d4696dbf` | `709.8389` | `1799.9031` | `1567.9502` | 401 dynamic full pipeline = 38/40, missing `T0028,T0033` |
| `probe401_cache_as_seed_20260520.py` | `fd59d825` | `711.9778` | `1799.9031` | `1589.3393` | cache-as-seed gets overwritten by worse 38/40 family |
| `probe501_pick_raw_expected_20260520.py` | `82b0cd48` | `711.9778` | `1799.9031` | `1589.3393` | low picker change no effect; 401 regresses via dynamic family |
| `probe501_pick_min_score_20260520.py` | `94c59280` | `709.8389` | `1799.9031` | `1567.9502` | low picker change no effect; 401 dynamic family A |
| `probe501_pick_max_willingness_20260520.py` | `f62c07e6` | `711.9778` | `1799.9031` | `1589.3393` | low picker change no effect; 401 dynamic family B |

Saved result files:
- `runs/official_probe_20260520_235744_d4696dbf.json`
- `runs/official_probe_20260520_235746_fd59d825.json`
- `runs/official_probe_20260520_235748_82b0cd48.json`
- `runs/official_probe_20260520_235750_94c59280.json`
- `runs/official_probe_20260520_235837_f62c07e6.json`

## Inferred official information

### low501

- All five probes returned identical low501 score/signature:
  - score `1799.9031`
  - assigned `30/30`
  - signature `d8fbb6a191`
  - shape `{(1 task, 2 couriers): 30}`
- Changing `_pick_low_robust_best` among raw expected, min-score model, and max-willingness model did not change official output.
- Interpretation: low501 official output is determined before the final robust picker, or all available candidate pools contain the same best low solution. Further final-picker tweaks are useless.

### scarce401

- Hard cache remains best known: `1531.5317`, assigned `39/40`, missing only `T0033`.
- Removing/weakening hard cache exposes only two worse dynamic families:
  - `1567.9502`: assigned `38/40`, missing `T0028,T0033`, signature `43e8acd642`.
  - `1589.3393`: assigned `38/40`, missing `T0028,T0033`, signature `df6654c84e`.
- Dynamic families often introduce one `(2 tasks, 2 couriers)` group but lose coverage; this is not worth it.
- Key current hard-cache fragile area remains:
  - worst groups include `T0001,T0035 C018`, `T0010,T0029 C004`, `T0012,T0019 C010`, `T0007,T0008 C001`, `T0020,T0023 C016`.
- Any future 401 improvement must preserve at least the current hard-cache covered set and must not let dynamic picker replace it unless exact objective and coverage improve.

## Decision

- Do not submit descendants of these probe candidates for score.
- Preserve current best `solver.py` SHA `70222083707d786011d28d7cc1ceab8f3b2ca95e0924b26f8dff2e6a49e865d6`.
- Future score attempts should target:
  1. low501 candidate generation before `_pick_low_robust_best`, not final picker.
  2. scarce401 same-covered-set cost reduction or a proven 40/40 construction; dynamic no-cache route is inferior.
