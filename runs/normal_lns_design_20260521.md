# Normal/Medium/High Algorithmic LNS Design

## Goal

Improve non-low/non-scarce cases from algorithmic structure, not historical output caches.

## Design

Build an offline large-neighborhood search harness around the current incumbent. Each iteration selects a window of 4-14 related tasks, removes all selected groups touching those tasks, and re-solves that window with a stronger column search than production uses. The repair accepts only if the original solver objective improves and coverage does not drop.

## Operators

1. Worst-cost window: high expected-cost groups.
2. Related-task window: tasks sharing candidate bundles/couriers.
3. Bundle-attractor window: tasks appearing in strong two-task bundle candidates.
4. Random deterministic windows seeded by input size.

## Why this is algorithmic

This is a true destroy-repair / LNS layer. It does not use official historical answers. It tests whether current normal path is locally saturated under larger windows and richer candidate columns.

## Integration rule

Do not integrate into `solver.py` unless the offline harness finds stable improvements on public/synthetic normal cases and runtime can be bounded.
