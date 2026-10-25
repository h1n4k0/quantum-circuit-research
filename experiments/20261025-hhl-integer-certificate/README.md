# HHL: integer-only full-domain numerical certificate

This package strengthens the **numerical evidence**, not the resource result,
for the preserved HHL octave-tensor circuit. Its source, constants and emitted
stream are unchanged. It does not recover any unavailable historical candidate.

## Result

The independently written integer datapath and directed arcsine enclosure cover
all **2,031,616** inputs `65536 <= X < 2097152`. For the modeled integer addend
`D(X)`, the maximum real-angle error in output units is rigorously enclosed by

```text
114661270223 / 2^28 <= max_X |D(X) - 2^32 asin(32768/X)|
                      <= 114661270226 / 2^28
```

The upper endpoint is approximately **427.1465175823 output units**, or exactly
`114661270226 / 2^60` radians (approximately **9.945279862318135e-8 rad**), below
the `1e-7` real-angle target. The largest upper bound occurs at `X=1886892`, with
addend `74590256`. Every interval determines a unique round-half-away-from-zero
real ideal; maximum integer error is **427**, inside the unchanged inclusive
429-unit task band. All those rounded ideals match the pinned grader expression
evaluated with this host's `math.asin`; portability to a different libm is not
assumed by the real-angle proof.

The independent addends equal the upstream integer model on every domain input.
This comparison happens **after** the integer certificate; it is optional and
is not an ingredient of the interval calculation.

Fresh replay of the preserved circuit and fair baselines gives:

| Actual circuit | Logical Toffoli | Peak logical qubits | TQ | Benchmark Clifford census |
|---|---:|---:|---:|---:|
| Pinned released upstream | 1348 | 115 | 155020 | 56419 |
| Recovered initial-001 | 1273 | 115 | 146395 | 14889 |
| Preserved octave-tensor | 1206 | 115 | 138690 | 13601 |

These are unchanged resources, not another cost reduction. Source and stored
stream official evaluations pass 8724 sampled shots. The unchanged strict audit
passes 71,424 gate cases across 7936 selector classes and three accumulator
regimes, checking every measurement outcome on those inputs through the upstream
affine ledger. The suffix component checker also passes. These gate checks are
**not an independent whole-circuit simulator or an all-accumulator theorem**.

## Why the enclosure is rigorous

Let `z=32768/X`, so `0 < z <= 1/2`. The positive power series is
`asin(z) = sum(n>=0) c_n z^(2n+1)`, with
`c_n=binomial(2n,n)/(4^n (2n+1))` and `0 < c_n <= 1`.
The series identity is [NIST DLMF 4.24.1](https://dlmf.nist.gov/4.24.E1).
The following tail and implementation bounds are derived here, not imported
from that source.

The code retains `n=0..31`. Its positive omitted tail obeys

```text
0 <= tail <= z^65/(1-z^2) <= 4/(3*2^65) < 2^-60.
```

Python's exact rational arithmetic generates floor/ceiling Q60 coefficients.
The C program bounds `z` by exact integer division, bounds `z^2`, and evaluates
the positive polynomial by Horner's rule. All lower products round down; all
upper products round up. Finally, one Q60 unit is added only to the upper bound
for the global tail. Monotonicity of addition and multiplication of nonnegative
numbers therefore preserves inclusion at every step. No floating-point
operations occur in the C certificate.

All scaled factors are bounded before multiplication; the products plus rounding
constants fit in unsigned 128-bit arithmetic. Integer datapath intermediates
fit in their signed 64-bit storage. The full-domain undefined-behavior-sanitized
build produces byte-identical records. Observed interval width is at most five
Q60 units, or `5/2^28` output units. A separate exact-`Fraction` recurrence checks
1205 selected values: every leaf endpoint, global endpoints, the worst witness,
and seeded random draws. Deliberately collapsed intervals, bad addends and
modified configurations are rejected. Those spot checks supplement, rather
than replace, the bound argument.

The datapath evaluator is written separately from the upstream model. It uses
an actual 15-bit cyclic rotation, an explicit Booth-recode truth table, signed
integer truncation rows, and checks all three curvature-window prefixes. It
imports no upstream Python, NumPy or simulator code. Its semantics are still
derived from the same circuit specification; this is independent implementation,
not an independent physical experiment or a machine-checked theorem.

## Reproduce

Core prerequisites: Python 3.10+ standard library and a C compiler supporting
`unsigned __int128` (tested GCC 14.2.0). No package installation, network access,
model service or key is needed. Do not run Python with `-O`, or disable C asserts.

```sh
python -B reproduce.py \
  --candidate PUBLIC/checkpoints/hhl-octave-tensor/candidate \
  --output NEW_DIRECTORY_OUTSIDE_ALL_FROZEN_INPUTS
python -B verification/test_certificate.py \
  --candidate PUBLIC/checkpoints/hhl-octave-tensor/candidate \
  --records NEW_DIRECTORY_OUTSIDE_ALL_FROZEN_INPUTS/certificate-records.bin \
  --output ANOTHER_NEW_DIRECTORY
```

The runner rejects modified source/constants, existing outputs, outputs within
candidate/package/protected manifest ancestors, and a modified package manifest.
The second command also requires compiler undefined-behavior sanitizer support.
Its failure logs remain in the new output directory; none is needed for the
published scientific reports.

Optional all-domain shared-model comparison adds `--upstream UPSTREAM`, requiring
NumPy and Click plus a clean `andigu/uncompute` checkout at
`64b5a13aa249f1360846657392e6c66817b26d0f`. To repeat the separate circuit evidence,
run the existing `PUBLIC/checkpoints/hhl-octave-tensor/reproduce.py` with that
checkout, `--snapshot PUBLIC/initial-001`, and a different fresh output directory.

The generated 48,758,784-byte record stream is not duplicated in this package.
It is deterministically regenerated and bound by SHA-256
`ce5838584fc1ae454acd54c9e4e2d5df69f91c2018b7ac0efe7cdfcc647a37e8`.
Every record is three little-endian uint64 values: addend, lower Q60 arcsine,
upper Q60 arcsine, in ascending input order. The generated header is also hashed.

## Scope, provenance and remaining gap

The new theorem is an **all-input numerical-model enclosure**. Source pinning and
the separately rerun gate evidence connect it to the circuit, but no new complete
gate-level proof over all inputs and all `2^33` accumulators is claimed. The
numerical model's additive output naturally defines a modular translation for
every accumulator; showing that the full gate implementation realizes that map
everywhere remains a separate obligation. Compiler correctness, integer-language
semantics and the explicit analytic argument are trusted. No hardware speedup,
energy saving, universal novelty, or global-optimum claim follows.

The datapath specification and input constants derive from Apache-2.0
`andigu/uncompute`; its unmodified license is included. Existing repository
attribution and `LICENSING.md` remain controlling: no blanket new license is
assigned to original verification code or documentation here. Results contain
no private paths, messages, credentials or authorization records.
