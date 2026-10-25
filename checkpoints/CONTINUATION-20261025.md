# Research continuation — 25 October 2026

The October 23 frozen checkpoint remains unchanged. New, separately scoped
experiments are indexed here; earlier unavailable source packages are not
treated as recovered or reproducible results.

## Coulomb: verified composition of the two saved tradeoffs

[Source, construction, reports and offline reproduction](../experiments/20261025-coulomb-composition/README.md)

| Source | Logical Toffoli | Peak logical qubits | T×Q | Benchmark Clifford |
|---|---:|---:|---:|---:|
| Saved partial-cache lookup | 1097 | 142 | 155774 | 7285 |
| Saved norm-parity alias | 1110 | 141 | 156510 | 6723 |
| **New actual composition** | **1097** | **141** | **154677** | **7292** |

The new combined source now exists and has fresh verification; the previous
checkpoint correctly described its two candidates as separate. It saves one
qubit relative to the partial-cache source while adding seven benchmark
Clifford operations. T×Q falls 0.7042% relative to that source and 4.4496%
relative to the pinned upstream 1140/142 circuit.

Fresh actual-stream parity-transfer, allocation-renaming and dirty-output
lookup certificates support composition of the interfaces. The strict audit
passes 837,822 selected coordinate/accumulator cases and the official grader
passes 9,017 sampled shots. The evidence is **not** a full all-coordinate,
all-accumulator proof of the complete circuit. The unchanged numerical
contract and all baseline comparison details are recorded in the package.

No hardware speedup, global optimum, physical T-count or new blanket license
is claimed. Existing licensing and upstream attribution remain in force.
