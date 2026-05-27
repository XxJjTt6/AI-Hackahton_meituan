# Research Notes 20:15 Global 10-Case View

External methods reviewed:
- PyVRP / Hybrid Genetic Search: route/column recombination with selective route exchange and local search.
- ALNS + set-partitioning hybrids: maintain a pool of route/column fragments and solve restricted set-partitioning to recombine.
- Stochastic matching / probabilistic set packing: relevant for low willingness, but only if new edge/column costs are available.

Mapping to current contest:
- We already mined historical official columns; global best from that pool is only around `706.197`, and unsafe cache validation proved hidden collisions can destroy score.
- To reach `700`, the missing ingredient is not recombining known columns; it is generating new low/scarce columns under hidden data.
- Clean future experiments must target new column generation inside safe `solver.py`, especially scarce bundle alternatives and low pair assignments, without altering proven large302/scarce cache behavior.
