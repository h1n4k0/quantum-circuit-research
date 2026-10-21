# Quantum circuit research

Independent, ongoing research into reproducible logical quantum-circuit optimization.
This project is not affiliated with or endorsed by Anthropic or the authors of the
upstream research. It does not claim certified state of the art.

The initial research window is **21–28 October 2026**. This repository starts with
a frozen, audited checkpoint rather than unreviewed work in progress.

## Initial checkpoint

| Task | Released circuit: Toffoli / qubits / TQ | Initial candidate: Toffoli / qubits / TQ | TQ reduction |
|---|---:|---:|---:|
| HHL angle | 1,348 / 115 / 155,020 | 1,273 / 115 / 146,395 | 5.56% |
| Coulomb inverse distance | 1,140 / 142 / 161,880 | 1,110 / 142 / 157,620 | 2.63% |

**T means logical Toffoli gates, not physical T gates.** Q is peak live logical
qubits. TQ is a resource proxy, not a measured runtime or physical-qubit estimate.
These are fixed-instance circuit improvements, not end-to-end algorithm claims.

The unchanged upstream graders accept both candidates. Additional tests cover
71,424 HHL gate-level cases and 837,822 Coulomb gate-level cases, using the
upstream simulator's strict affine phase ledger for all measurement outcomes on
each tested input. These tests are **not a complete proof over every input and
accumulator**. See the [checkpoint and exact limits](initial-001/RESEARCH_SNAPSHOT.md).

## Reproduce and inspect

- [Frozen checkpoint: source, reports, reproduction commands](initial-001/RESEARCH_SNAPSHOT.md)
- [Benchmark definitions and evidence requirements](BENCHMARKS.md)
- [Provenance and attribution](PROVENANCE.md)
- [Research status and release policy](STATUS.md)
- [Licensing scope](LICENSING.md)

Run the checkpoint's reproduction commands from `initial-001/`. The upstream
repository is fetched separately and pinned to
`64b5a13aa249f1360846657392e6c66817b26d0f`; its evaluator, contracts and precision
requirements are unchanged. No LLM API is needed to reproduce this checkpoint.

## Sources

- Gu, Kemeny, Yelin and Lukin, [*Discovering state-of-the-art quantum circuits with large language models*](https://arxiv.org/abs/2610.22367v1).
- [Upstream code at the pinned commit](https://github.com/andigu/uncompute/tree/64b5a13aa249f1360846657392e6c66817b26d0f).
- Anthropic, [*Designing more efficient quantum circuits with Claude*](https://www.anthropic.com/research/designing-efficient-quantum-circuits).

The paper's title describes the upstream work; it is not a claim about this repository.
