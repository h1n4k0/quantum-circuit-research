# HHL phase-only checkpoint: 1206 Toffoli / 115 qubits

This checkpoint changes only the final measurement-phase repair of the public
`initial-001/candidates/hhl/anf_v1` circuit. Its numerical constants and executable
arithmetic prefix are unchanged. It is a new reproduced implementation, not a
claim to have recovered any unavailable later experiment.

| Actual straight-line circuit | Toffoli | Qubits | TQ | Benchmark Clifford census |
|---|---:|---:|---:|---:|
| Pinned upstream released | 1348 | 115 | 155020 | 56419 |
| Public initial-001 | 1273 | 115 | 146395 | 14889 |
| This checkpoint | **1206** | **115** | **138690** | **13601** |

This is 67 fewer Toffolis (5.2632%) than initial-001, or 142 fewer (10.5341%)
than the released circuit at the same qubit budget. The benchmark census counts
upstream CX/CZ/SWAP/R/HMR operations, not all physical Clifford work. The circuit
references 7363 outcome IDs; that is **not** simultaneous classical memory.
These are logical benchmark resources, not a hardware-runtime claim.

## Construction

Each octave uses its actual smallest leaf width to define a local coefficient
truth table. A packed-word algebraic normal form is split into two variable
sets. One monomial bank includes the octave flag; the other is unconditioned.
Conditioned Z/CZ gates read out the coefficient measurement parities. Left
monomials are visited depth-first and measured/phase-corrected before their
parents; the right bank stays live until those corrections finish.

The five local banks cost 20, 17, 12, 10 and 8 nonlinear features. Three octave
flags give **70** total phase-repair Toffolis, replacing the initial 137. All
polarities and nontrivial variable splits were enumerated for this construction,
with a deterministic greedy parent-closure rule. This is **not** a global
optimality theorem, nor an optimal monomial-DAG theorem. No novelty claim is
made for split-monomial phase repair, temporary-AND cleanup, or this general
technique.

`candidate/phase_plan.json` is load-bearing input to the emitter. The arithmetic
coefficient table is `candidate/constants.json`. The selected plan is regenerated
by the reproduction command. Discovery scripts and two earlier finite negative
screens are included. Their direct generator creates an experimental source;
the frozen source additionally replaces its descriptive module docstring and
removes the inherited obsolete stored stream. The verified new stream is the
included `candidate/circuit.ops.xz`.

## Reproduce

Use a clean checkout of `andigu/uncompute` at commit
`64b5a13aa249f1360846657392e6c66817b26d0f` and the public repository's
`initial-001` directory. Required: Python, NumPy and Click. Tested versions:
Python 3.12.14, NumPy 2.3.5, Click 8.4.2. The upstream C evaluation kernel was
built locally with `make -C UPSTREAM kernel`; no network/model service is used
by these tests.

```sh
python reproduce.py --upstream UPSTREAM --snapshot PUBLIC/initial-001 \
  --output NEW_DIRECTORY_OUTSIDE_ALL_FROZEN_INPUTS
```

The command rejects modified tracked upstream files, pins the original audit,
rejects existing/protected output paths before creating them, reproduces both
baselines, runs source and stored-stream official tests, compares their bytes,
runs the strict audit and independent suffix checker, and regenerates the exact
selected plans. It does not install software or write to the inputs. It is safe
to put the checkpoint in a larger manifest-protected repository container.

## Verification scope

* Fresh official source and stored-stream tests pass; these are **sampled**.
* The unchanged original audit checks all 2,031,616 numerical-model inputs and
  71,424 strict gate cases: every 7936 selector class, lower-byte values
  0/127/255, and accumulator zero/all-ones/wrap-seam. Its affine draw ledger
  covers all measurement outcomes **for those tested basis inputs**.
* The numerical report gives maximum integer error 427 output units and
  floating-point real error about 9.9452798663e-8 rad. This checkpoint does not
  replace that oracle with a rigorous directed-interval proof.
* The independent suffix interpreter never executes upstream `Simulator`.
  It reconstructs packed words directly from integers and checks the **actual
  emitted suffix** on all 7936 valid selector classes and all 50 initial
  coefficient outcomes plus 70 fresh suffix outcomes. It validates canonical
  operations, workspace last-reset/measurement entry, unknown inherited
  outcome rejection, all wire restoration, and a missing-CZ mutation.
* That component proof explicitly assumes the incoming phase equals the 50
  coefficient measurement debts. It is not an independent whole-prefix proof.
  Lower eight X bits and every accumulator wire are structurally untouched by
  the suffix. Invalid selectors are excluded rather than assigned a promise.
* There is **no complete gate-level all-2^33-accumulators theorem** in this
  checkpoint. The whole-circuit audit uses the upstream simulator and numerical
  model; independent reruns of that same code are not independent engines.

## Provenance and limitations

Source and copied arithmetic helpers derive from the Apache-2.0 upstream and
public initial-001; preserve `UPSTREAM_LICENSE` and the repository `LICENSING.md`
scope. No blanket license is assigned here to original verification scripts or
documentation. No upstream root NOTICE existed at the pinned commit. Exact source, constants,
plan, raw stream and verifier hashes are in the reports and manifest. No private
messages, credentials, account data or internal storage paths are included.
The first package QA reached all scientific checks, then rejected Python tuples
versus JSON lists in plan equality. A JSON-normalized comparison corrected only
that packaging check; a fresh whole command passed afterward. The failed runner
and log remain in the private work record, not silently overwritten.
