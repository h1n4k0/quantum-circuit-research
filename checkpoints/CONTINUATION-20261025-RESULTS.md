# Verified research results — 25 October 2026

The bounded experiments in this batch are complete and their packages are
frozen. Prior checkpoint files remain unchanged. All results below concern
logical circuits and computational evidence, not hardware performance.

| Task | Preserved October 23 source | New verified source | Change |
|---|---|---|---|
| HHL | 1206 Toffoli / 115 qubits | **1205 / 115** | One fewer Toffoli; benchmark Clifford remains 13601 |
| Coulomb | Separate 1097 / 142 and 1110 / 141 | **1097 / 141** | Actual composition; seven more Clifford operations than the 1097/142 source |

HHL T×Q is **138575**, 0.0829% below the preserved octave-tensor source and
10.6083% below the pinned released upstream 1348/115 circuit. Coulomb T×Q is
**154677**, 0.7042% below the preserved partial-cache source and 4.4496% below
the pinned released upstream 1140/142 circuit. Metrics from different sources
are not combined; each table row has an actual source and operation stream.

## Packages

1. [Coulomb composition](../experiments/20261025-coulomb-composition/README.md):
   actual parity-alias/partial-cache composition, deterministic constructor,
   837,822 selected strict gate cases, 9,017 sampled official shots, and scoped
   interface/lookup proofs. Independent resource and allocator replay confirms
   1097 Toffoli, 141 peak qubits and 7292 benchmark Clifford operations.
2. [HHL numerical certificate](../experiments/20261025-hhl-integer-certificate/README.md):
   integer-only datapath and directed Q60 arcsine bounds for all 2,031,616
   numerical inputs. Maximum real-error upper bound is exactly
   `114661270226/2^60` radians, below `1e-7`. All rounded real ideals are unique;
   maximum integer error is 427 within the inclusive 429-unit contract.
3. [HHL single-shear phase repair](../experiments/20261025-hhl-single-shear/README.md):
   a reversible `X12 ^= X16` coordinate change around one phase-repair block
   saves one nonlinear feature. A finite 219-choice single-shear screen is
   preserved, with its greedy-DAG limitations. Actual 1205/115 emission passes
   8,735 sampled official shots, 71,424 strict gate cases and the independent
   suffix checker over all 7,936 valid selector classes and all measurement
   outcomes under its incoming-phase contract.

The numerical certificate transfers to the new HHL source through both
executable-prefix identity and exact emitted-prefix equality. Independent
review additionally replays all tests, reconstructs every selector polynomial,
counts actual gates and live wires, and confirms that omitting the entering
frame CX breaks phase repair while omitting the exiting CX breaks wire
restoration. [Review and bound reports](../independent-review/20261025-hhl-single-shear/review.json).

## Remaining limitations

There is still no complete gate-level theorem over all task inputs and all
accumulators. Full-domain **numerical-model** evidence and conditional component
proofs are distinct from that missing whole-circuit result. The strict gate
tests share the pinned upstream simulator; independent reviewers disclose
where they rerun rather than independently reimplement it. Compiler and
integer-language semantics remain trusted by the C certificate.

No global circuit optimum, physical T-count, physical classical-memory minimum,
fault-tolerant runtime or hardware speedup is claimed. Unavailable historical
lower-count sources have not been recovered and are not included in these
reproducible results. Preparation failures and the limited negative search
results are retained. Existing licensing and attribution remain unchanged.
