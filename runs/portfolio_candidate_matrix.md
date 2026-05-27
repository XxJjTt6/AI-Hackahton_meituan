# Portfolio Candidate Matrix

Hard rule: evaluate whole 10-case portfolio, not a single sample.

| Candidate | Low | Scarce | Large | High | Expected official avg | Submit? |
|---|---|---|---|---|---:|---|
| `solver.py` / `41db4b34` | official best observed | official best observed | official best observed | safe | 706.4264 | baseline |
| `52daa29b` | same | regressed to 1589.3393 | same | no high gain | 712.2072 | blacklisted |
| `candidate_sla_scarce_pick1081.py` | same on calibrated | proxy sometimes better, official hard-cache likely same | local stable | same | ~706.4264 | no clear gain |
| high-only patches | same | timing/layout regression risk | risk | sometimes intended gain | <706.426 only if no regress | do not submit |

Remaining attempts: 2.

Submission rule: require direct evidence of total score reduction >= 10 and no known regression path.
