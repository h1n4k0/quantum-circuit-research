# Coulomb initial-001 fresh replay (22 October 2026)

This checkpoint reproduces, rather than improves, the published initial-001
Coulomb circuit: **1110 logical Toffoli / 142 peak logical qubits / TQ 157620**.
The fresh emitted stream is byte-identical to the stored public stream
(SHA-256 `17d49bccb9ae180982a3d0fb904e4d0d14da27e496f00da4cdc943968c182440`).
No missing later circuit or historical proof is reconstructed or reused.

## Fresh evidence

- Unchanged official evaluator: 9018 shots and zero failed output, phase, or cleanliness checks.
- Public independent audit rerun: 837822 strict gate-level cases, covering 139637
  attainable norms, one magnitude witness in both orientations, and three accumulator
  values per orientation. The affine phase ledger checks every measurement record
  for those tested basis inputs.
- Integer inverse-square-root oracle over all 195075 positive norms; maximum
  rounded error 32. This is not a proof over all coordinate pairs or all accumulators.
- Upstream fixed to `64b5a13aa249f1360846657392e6c66817b26d0f`; task contract,
  grader and reference are byte-identical. The simulator is shared upstream code.

## Reproduce

Use a new output directory outside this frozen checkpoint and an unchanged clone
of the pinned upstream. From this checkpoint directory, with absolute UPSTREAM
and OUT environment variables and Python 3.10+, NumPy and Click installed:

```sh
mkdir -p "$OUT"
make -C "$UPSTREAM" kernel
PYTHONPATH="$UPSTREAM" UNCOMPUTE_KERNEL=1 python "$UPSTREAM/tools/eval.py" coulomb-potential --circuit "$PWD/task/circuits/baseline/circuit.py" --capture "$OUT/baseline_emitted.ops" --out "$OUT/official"
python verification/audit_coulomb_candidate.py task/circuits/baseline/circuit.py --upstream "$UPSTREAM" --output "$OUT/independent.json"
```

The candidate is inside a copied task tree, preserving the unmodified contract
loader. `bind_baseline_reproduction.py` additionally checks existing reports in
its stated workspace layout (see CLI); it does not itself run the simulator.
Original attribution and licensing scope are preserved: see the parent repository
LICENSING.md and UPSTREAM_LICENSE. No blanket new license is assigned here.
