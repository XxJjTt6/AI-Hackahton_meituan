# Experiment Status 23:40 Bold Iteration

User allowed bold local edits; best safe version saved externally.

Tried and rejected:
- `candidate_bold_runtime_search_work.py`: high patch + low MCF; low calibrated same sig and faster, but public large still wobbles, size 79.3KB, not enough gain.
- `candidate_bold_compact_high_work.py`: compact high + low MCF; preflight public large 11.51s, reject.
- `candidate_scarce_bold_no_low.py`: made scarce hard cache a candidate instead of immediate return; scarce proxy sometimes improves but has 16s/10s runs and no stable official-safe evidence, reject.
- `candidate_low_picker_will_heavy.py`: worsens low020, reject.
- `candidate_low_force_k2_safe.py`: no-op on proxies, reject.
- `candidate_low_k2_mcf_only.py`: sometimes K2 but worse cost and timeout, reject.
- `candidate_low_bias_active_alpha.py`: K2-like but significantly worse, reject.

Held only as low-value fallback:
- `candidate_high_compact_only.py` / `candidate_trim_high_combo.py`: expected avg gain only 0.229, below threshold.

Next direction:
- Build a separate larger low exact/top-pair search prototype without size constraints first; only minify into solver if it beats calibrated/proxy low substantially.

Additional after continue:
- `candidate_scarce_pair_dp_work.py`: embedded DP too slow; direct call covers only 22 tasks in 3.2s, not viable.
- `candidate_scarce_pair_greedy_work.py`: fast but public scarce cost `1443.5`, worse than current `1097.8`; picker correctly rejects.
- Scarce observed-column local replacement around worst groups only reproduces current `1531.5316`.
- Low K2 BnB top80 found complete K2 `1247.4`, worse than current calibrated `1199.1`.

Implication: current local objective is saturated; remaining path needs a different official-objective inference, not more search under current expected-cost model.

Late candidates:
- `candidate_minify_high_compact.py`: safest held high-only compact, sha `52daa29b`, expected avg gain `0.22941`, below threshold.
- `candidate_low_hard_output_speed.py`: strict low official output speed cache + high compact; synthetic low did not false-trigger, but public large preflight 10.61s/657.44, reject.

Current best actionable file remains `solver.py` safe main; do not submit low hard speed or pair-DP candidates.
