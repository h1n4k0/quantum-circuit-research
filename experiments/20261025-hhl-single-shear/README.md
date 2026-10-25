# HHL single-shear phase repair: 1205 Toffoli / 115 qubits

This finite experiment makes one reversible CX coordinate change within the
preserved octave-tensor phase suffix. The executable arithmetic prefix, numerical
constants, task contract and accumulator behavior being tested are unchanged.

| Freshly emitted circuit | Logical Toffoli | Peak logical qubits | TQ | Benchmark Clifford census |
|---|---:|---:|---:|---:|
| Pinned released upstream | 1348 | 115 | 155020 | 56419 |
| Preserved octave-tensor | 1206 | 115 | 138690 | 13601 |
| This single-shear candidate | **1205** | **115** | **138575** | **13601** |

The change saves **one Toffoli**, or 0.0829% TQ versus the preserved octave-tensor
source; it is 10.6083% below the released baseline TQ. The benefit is small and
is not rounded into a larger claim. Outcome-index references decrease from 7363
to 7327 and expanded operations from 28659 to 28588; neither is a physical-memory
or runtime measurement. The Clifford column is the benchmark's limited census.

## Construction and finite search

For octave exponent 18, the local address is `X[11:18]`. Temporarily replace
`X12` by `X12 XOR X16`, evaluate the exact coefficient-table ANF in that basis,
then undo the same CX. A polarity/partition search now uses seven conditioned
left features plus four unconditioned right nonlinear features, versus eight
plus four before. The other four octaves are unchanged. The five banks cost
`20,17,11,10,8`; adding three octave flags yields **69** phase-repair Toffolis,
previously 70. The actual emitter, not just this count, is evaluated below.

The exact-table screen tried no shear and every directed one-CX shear separately
within each octave: **219** octave/coordinate choices, with every polarity and
every nontrivial two-way variable partition for each. It uses the prior
deterministic greedy monomial-parent closure, not an exact minimum-DAG solver.
No lower Toffoli count was found for the other four octaves in this finite screen.
This is **not a global optimum** over linear maps, Boolean circuits or quantum
implementations. The construction uses standard reversible basis changes and
ANF phase readout; no general-technique novelty claim is made.

`construction/upper-octaves.json` and `lower-octaves.json` record the complete
finite screen summaries and best exact plans. The constructor deliberately
adopts only strict feature-count improvements, not equal-count alternatives.

## Verification

* Fresh source and stored-stream official tests pass **8735 sampled shots**.
  Emitted bytes are identical, SHA-256
  `709a93012bbc4f43ae4ea44457f72219fafecdab9f4fe2ab626e4ca8f359f05d`.
* The unchanged strict audit passes all 2,031,616 numerical-model inputs and
  **71,424 gate cases**: 7936 selector classes, three lower-byte patterns and
  three accumulator regimes. Its affine ledger covers all outcomes **on those
  tested inputs**; it shares the upstream simulator/model.
* The independent suffix interpreter passes **all 7936 valid selector classes**,
  50 independent incoming coefficient measurements and 69 fresh suffix draws.
  It checks actual emitted gates without executing upstream `Simulator`, restores
  every touched wire, structurally excludes the lower eight X bits and all
  accumulator wires, and rejects a missing-CZ mutant. Its precondition is the
  stated incoming coefficient phase debt and clean workspace, not a new proof
  of the arithmetic prefix.
* A new transfer checker establishes both executable-prefix AST identity and
  **byte-for-byte expanded arithmetic-prefix identity** with the preserved
  octave-tensor source. Instrumented and uninstrumented builds agree; coefficient
  outcome IDs and persistent registers agree. This transfers the separately
  reproduced integer-only numerical certificate: all-domain maximum real error
  is at most exactly `114661270226/2^60` rad, below `1e-7`, and integer error is
  at most 427. It does not turn that numerical-model bound into a complete
  gate-level all-input/all-accumulator theorem.
* Fresh replay re-emits both baselines, regenerates the constructor byte-for-byte,
  reruns the full polarity/partition search for the selected shear, checks all
  manifest-frozen inputs before and after, and invokes the separate numerical
  certificate from source. Direct guard tests reject existing/protected outputs.

## Reproduce

Use Python with NumPy and Click, a C compiler supporting unsigned 128-bit
integers, the published integer-certificate package, and a clean
`andigu/uncompute` checkout at `64b5a13aa249f1360846657392e6c66817b26d0f`.
No network, installation, model service or key is used. Keep assertions enabled.

```sh
python -B reproduce.py --repository PUBLIC --upstream UPSTREAM \
  --numeric-certificate HHL_INTEGER_CERTIFICATE_PACKAGE \
  --output NEW_DIRECTORY_OUTSIDE_ALL_INPUTS
python -B verification/verify_guards.py \
  --repository PUBLIC --upstream UPSTREAM \
  --numeric-certificate HHL_INTEGER_CERTIFICATE_PACKAGE \
  --output ANOTHER_NEW_DIRECTORY
```

The baseline source is staged into a complete task before loading it, so its
unchanged contract lookup has a `grader.py` ancestor. To rerun the entire finite
screen rather than only the selected shear search, use:

```sh
python -B construction/screen.py \
  --constants PUBLIC/checkpoints/hhl-octave-tensor/candidate/constants.json \
  --exponents 16 17 18 19 20 --jobs 4 --output NEW_SCREEN_JSON
```

Screen timing is environment-dependent; it is not part of source construction
or a quantum speedup claim. Package reports retain the exact source hashes.
Two initial checker invocation failures are retained in
`results/preflight_failures.json`: an output guard rejection, then a missing
task-ancestor rejection. Neither changed the scientific source; a correctly
staged external-output invocation subsequently passed.

## Scope and attribution

The original gap remains: no complete gate-level theorem over all X and all
`2^33` accumulators is claimed. No hardware experiment, physical memory saving,
fault-tolerant runtime, global optimality or recovered lost-source claim is made.
The frozen benchmark is the fair released comparator, not an older expensive
construction. Standard-library/C numerical verification and actual emission
checks strengthen evidence but are not a proof-assistant development.

Candidate source/helpers derive from the Apache-2.0 upstream through the
preserved public octave-tensor checkpoint. `UPSTREAM_LICENSE` is unchanged;
preserve upstream attribution. The repository's `LICENSING.md` scope remains
unchanged, with no blanket license newly assigned to original research code or
documentation. No private paths, messages, credentials or authorization records
are included. The finite experiment ends at this reviewed checkpoint.
