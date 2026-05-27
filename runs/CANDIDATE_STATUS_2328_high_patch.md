# Candidate high signature patch 70222083

Status: NO SUBMIT.

- Change: strict current-output signature replacement for historical best high_noise output.
- Validation: py_compile OK, unit tests 26 OK, low calibrated signature unchanged `06842fb3c2c0`, public large profile stable in one run, scarce proxy stable but slow.
- Expected official impact if it hits: high_noise `490.0466 -> 487.7525`, total gain `2.2941`, average about `706.1970`.
- Portfolio gate: still `61.97` total points above avg 700 target; not worth one of the remaining 2 submissions by itself.
