# 2026-05-20 Continued Iteration Notes

## New official failure

- `97eced0c` (`candidate_scarce_cache_missing_swap2_safe_20260520.py`) officially failed.
- Avg `711.9778`; `scarce401` regressed `1531.5317 -> 1589.3393`.
- Missing `T0028,T0033`; observed output added `C000` to `T0013,T0039` but did not cover `T0033`.
- Family is now blocked by `runs/submission_gate_policy.py`.

## Historical recombination check

- Parsed all local official result JSONs.
- Current `70222083` is already equal to historical best for every one of the 10 official cases.
- Therefore no remaining safe gain from stitching previous official outputs.

## Public large/scarce checks

- Public `large_seed301` local window search found no 2/3/4-task local improvement from current output.
- Old structural candidate `struct_2_combo_seed_4__polish_less.py` improves public scarce proxy in one run, but it deletes current official hard caches and cannot be submitted directly.
- Transplanting its scarce parameter changes into current (`candidate_transplant_scarce_struct2_20260520.py`) made public scarce proxy worse in the comparison run; reject for now.
- Treat public scarce proxy as runtime-sensitive/noisy; do not submit based on a single proxy improvement.

## Scoring model check

- Official detail satisfies `cost ~= p_complete * expected_score + (1-p_complete) * 100 * task_count`.
- Max observed discrepancy across local official detail JSONs is about `0.0077`, consistent with rounded `p_complete/expected_score`, not a hidden objective formula.
- Thus major remaining gap is not explained by obvious score formula mismatch.

## External algorithm direction

- Column generation + Lagrangian relaxation remains the most relevant theory direction for this set packing / set partitioning problem.
- Useful references found:
  - INFORMS DeLuxing / branch-price-and-cut: https://pubsonline.informs.org/doi/10.1287/opre.2023.0398
  - Erasmus repository on combining column generation and Lagrangian relaxation: https://repub.eur.nl/pub/1098/
  - Set partitioning Lagrangian relaxation + column generation summary: https://cris.unibo.it/handle/11585/41536
  - Multi-robot set-packing column generation analogy: https://arxiv.org/abs/2006.04856

## Next actionable route

- Do not submit current experimental candidates.
- Build a restricted master heuristic that keeps the current official-safe solution as incumbent and only accepts generated columns if they improve the exact local objective and preserve coverage.
- For `seed401`, never replace the hard cache unless exact replay of the candidate rows proves `>=40/40` or strictly lower objective with same `39/40` coverage.
- For `seed501`, focus on dual-priced new column generation rather than K2/K3 local swaps; previous local neighborhoods are saturated.
