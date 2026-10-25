# Composed Coulomb lookup and norm-parity alias

This is a new composition of two separately published October 23 sources.
Their original files and reports remain unchanged. It is not a recovery of
any unavailable earlier experiment.

| Circuit | Logical Toffoli | Peak logical qubits | T×Q | Benchmark Clifford |
|---|---:|---:|---:|---:|
| Released upstream discovered circuit | 1140 | 142 | 161880 | 7253 |
| Recovered initial-001 | 1110 | 142 | 157620 | 6716 |
| Published norm-parity alias | 1110 | 141 | 156510 | 6723 |
| Published partial-cache lookup | 1097 | 142 | 155774 | 7285 |
| **New composition** | **1097** | **141** | **154677** | **7292** |

The composition has the same Toffoli count and one fewer qubit than the
partial-cache source, at the cost of seven extra benchmark Clifford operations.
Its T×Q is 0.7042% lower than that source, 1.8671% below initial-001 and 4.4496%
below the pinned released upstream circuit. These are logical-resource
comparisons, not physical T-count, elapsed-time, or hardware-speed claims.
The two immediate predecessor sources and new source are freshly re-emitted
and evaluated together by `reproduce.py`; the first two historical rows are
the pinned comparisons defined in the repository's `BENCHMARKS.md` and the
preserved initial reports. No global optimality or novelty claim is made.

## Why the changes compose

The norm-parity transform transfers the least-significant squared-distance
bit into a magnitude LSB, releases the old norm wire during the middle of the
computation, and restores both representations before inverse squaring.
The partial-cache transform changes only the forward lookup within that
middle. The new construction takes the exact published parity source and
replaces its forward lookup with the exact published partial-cache helper,
plan and invocation. Its explanatory header is updated; the other executable
code is not changed. `construction/compose.py` pins both antecedent hashes
and deterministically recreates the new bytes.

This is not merely adding resource savings on paper. Fresh actual-stream
checking proves that the entire new middle equals the partial-cache source's
middle under an allocation-aware wire renaming. The prefix and suffix are
byte-for-byte gate-equal, 7,280 middle gates and 217 temporary allocations
match, and all eight parity assignments round-trip. The six nonneutral
omitted-CX mutations are rejected. The parity checker's baseline pin was
adapted from the previous checker to the partial-cache source; it is not an
independently implemented whole-circuit simulator.

The lookup component is also checked again on the actual composed stream:
all 128 physical addresses, all 2^24 dirty output assignments through a
fail-closed affine-output grammar, and all 27 independent HMR draws through
a symbolic phase ledger. The actual allocator enters/exits with the same
121 live qubits and peaks at 141. Representative omitted CX, CZ and CCX
mutants are rejected. These checks do not assume old physical wire numbers.

## Fresh evidence and its limits

* `results/official_report.json`: unchanged official evaluator, 9,017 sampled
  shots, zero output, phase/sign or dirty-qubit failures, stream-bound counts.
* `results/strict.json`: independent integer oracle for every 195,075 positive
  norm; 837,822 selected gate cases covering one magnitude witness for each
  of 139,637 attainable norms, both orientations, and three accumulator values.
  All measurement outcomes are covered by the affine ledger **on those inputs**.
* `results/parity_composition.json` and `results/lookup_component.json`:
  source-bound component and allocation certificates described above.
* Numerical table and task contract are unchanged. The rounded error remains
  at most 32; `32.5 / 2^24 < 2e-6` bounds the real error as in the initial audit.

This does **not** prove the complete circuit for all coordinate pairs or all
2^25 accumulator inputs. Whole-circuit tests use the same pinned upstream
simulator/model infrastructure as before. Component proofs have explicit
interface assumptions and do not silently upgrade the whole-task guarantee.
The evaluator's outcome-index count is not peak classical memory.

The two failed preparation invocations are preserved separately: a malformed
manually transcribed source pin failed closed before construction, and the
first parity-checker invocation lacked a staged task ancestor for its baseline.
Neither was a passing scientific test; neither produced a candidate
counterexample. Subsequent successful checks use the corrected pin and an
exact staged baseline with the pinned task files.

## Reproduce offline

Use Python 3.12 with NumPy and Click, plus the pinned upstream's normal local
C build prerequisites. No model service, network request, or hardware run is
needed. Start from this research repository and a clean complete
`andigu/uncompute` checkout at
`64b5a13aa249f1360846657392e6c66817b26d0f`.

```sh
python -B experiments/20261025-coulomb-composition/reproduce.py \
  --repository /path/to/quantum-circuit-research \
  --upstream /path/to/pinned-uncompute \
  --output /path/to/new-output
```

The output must not exist and must be outside all repository, package,
upstream and manifested input directories. The runner verifies the manifest,
clean upstream pin and byte-equal task definitions; reconstructs the source;
re-emits all three sources and compares their stored streams; evaluates all
three; reruns both component certificates and the strict audit; and checks
that the package was unchanged. Output logs may contain local paths and are
not part of the public scientific reports.

Source SHA-256:
`e3d39c6bbfa8b6a9b45cf082dcc8cac1f0139d4ffbb60387bf1e84125d087b5b`.
Raw operation stream SHA-256:
`b8c6cdb00b03f0c22c657164bf9e19a5f06ed34ab42e7ea6a42f3a95c11f4792`.

The source derives from Apache-2.0 upstream code; `UPSTREAM_LICENSE` is
preserved. Repository `LICENSING.md` continues to govern the scope of
original contributions. No blanket new license is assigned here.
