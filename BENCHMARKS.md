# Benchmark definitions

The normative task definitions, graders and accuracy contracts are those in
`andigu/uncompute` at commit `64b5a13aa249f1360846657392e6c66817b26d0f`.

| Benchmark | Upstream task | Comparison circuit | Toffoli | Peak logical qubits | TQ |
|---|---|---|---:|---:|---:|
| HHL angle | `tasks/hhl-angle` | `circuits/discovered` | 1348 | 115 | 155020 |
| Coulomb inverse distance | `tasks/coulomb-potential` | `circuits/discovered` | 1140 | 142 | 161880 |

The comparison is against the released discovered circuits, not older and more
expensive constructions. TQ reduction is `1 - candidate_TQ / released_TQ`.
Toffoli and Clifford counts, qubits, classical outcomes and emitted operations
are distinct resource measures. Improvements in TQ do not imply every measure
improves. The evaluator's classical outcome index count is not physical memory.

## Publication evidence

A promoted candidate must record:

1. Upstream commit, unchanged task contract, source and constants hashes.
2. Emitted operation-stream hash, logical costs and unchanged-grader report.
3. Explicit test counts, input coverage, precision and accumulator assumptions.
4. Phase and ancillary-cleanliness checks, including their coverage limits.
5. Reproduction commands, dependencies, attribution and known negative results.

An official grader pass is sampled correctness evidence, not a mathematical
certificate of every input. Independent test design may still share upstream
simulator or numerical-model code; this dependency must be stated explicitly.

No physical hardware experiment, fault-tolerant runtime, energy saving, universal
novelty or certified state-of-the-art claim follows from these logical counts.
