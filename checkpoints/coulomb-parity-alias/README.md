# Norm-parity alias: fresh 1110 / 141 Coulomb checkpoint

Relative to the freshly replayed initial-001 source (1110 / 142), this source
uses **1110 logical Toffoli, 141 peak logical qubits, TQ 156510**, and **6723**
benchmark Clifford operations (previous 6716). It saves one persistent logical
wire, not any Toffoli. Source SHA-256 is
`bdbb62ac7537393aec212cb657aceeacdd5d15be3ebec9a5e30a456954cdccb4`.

## Representation and proof scope

After squaring, norm bit zero is the XOR of the three magnitude LSBs. Three CX
copy that parity into the first magnitude LSB and clear the original norm wire,
which is recycled. All middle operations use the new norm tuple; the remaining
coordinate and sign wires are protected. Before inverse squaring, the original
slot is reclaimed clean, three CX return the norm and magnitude bits, and the
original inverse square runs unchanged. `reclaim` is the existing upstream API,
not a modified allocator or a quantum gate. The seven-operation cost increase
is six CX plus the zero reset used when releasing the old slot.

The component proof uses the actual stream: seven-CX backward dependency cone
supplies parity for every magnitude input; eight assignments prove borrow and
return; six omitted-CX mutations are rejected. All 6724 middle gates and 310
temporary allocations match the baseline under an allocation-aware wire
bijection, including every classical outcome operand. Prefix and suffix are
exactly equal. This establishes the changed interface, not a new proof of the
baseline task over all coordinate pairs or all accumulator values.

Fresh official testing passed 9015 shots. The independent integer-oracle audit
passed 837822 gate cases: one witness for each of 139637 attainable norms,
both coordinate orientations, three accumulator values. All measurement
records are checked by the shared upstream affine ledger on those inputs.
Maximum rounded error remains 32. The original table, approximation, contract,
and upstream semantics are unchanged.

## Reproduce safely

Pin upstream `andigu/uncompute` at
`64b5a13aa249f1360846657392e6c66817b26d0f`. Python, NumPy, Click, make and a C
compiler are required. Use an absolute NEW output directory outside the entire
containing checkpoint collection. The runner checks the frozen manifest,
rejects existing/protected outputs before creating directories, compiles the
pinned kernel, reruns official + independent + interface checks, compares the
emitted stream, and rechecks the manifest.

```sh
python -B run.py --upstream /absolute/pinned/upstream --output /absolute/new/output
```

The first component-checker version incorrectly expected a unique
`un-squarer` phase mark; the mirror records its exit restoration too. It rejected
before emitting a report. Version 2 selects the first entry mark while retaining
all stream comparisons. This was a checker preflight failure, not a candidate
failure or a discarded counterexample.

Upstream attribution is retained in the source and UPSTREAM_LICENSE. Licensing
scope is inherited from the parent repository's LICENSING.md; no blanket new
license is assigned here. Published initial-001 is the only source antecedent;
no lost later implementation or certificate is claimed as recovered evidence.
