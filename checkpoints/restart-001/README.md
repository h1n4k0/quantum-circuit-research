# Restart checkpoint 001: published baseline identity

This checkpoint resumes work from the **existing, published** `initial-001`
commit `b6e0080c1eb45e2c3c62602527bb6f325c096342`. It verifies all 27 original
files (233,306 bytes), their Git blobs and complete original Git tree, both
original SHA-256 manifests, and the integrity of the two compressed operation
streams. New checkpoint files are intentionally outside that original allowlist.

## What is and is not established

The identity check is fresh. The historical reports record HHL **1273 Toffoli /
115 logical qubits** and Coulomb **1110 / 142**. They have **not** been rerun by
this checkpoint. Their bounded input, accumulator, measurement-ledger, and shared
simulator limitations remain as documented in `initial-001/RESEARCH_SNAPSHOT.md`.
Later unpreserved experiments are not a runnable baseline and are not claimed as
recovered or reproduced here. A hash or a remembered metric is not source code.

No code in the restored candidate or verification modules is imported or run by
the identity checker. Decompressing an operation stream only checks byte integrity.

## Reproduce this check

Python 3.9+ standard library only, from the repository root:

```sh
python checkpoints/restart-001/verify_initial_identity.py . \
  --output /tmp/initial-identity-new-result.json
```

Choose a new output path outside the checkout. Existing outputs are refused.
The result records the verifier and identity-manifest hashes. The committed
result was generated against the recovered original 27-file snapshot, before
this checkpoint was added; adding checkpoint files does not alter that allowlist.

## Continuity and publication discipline

Subsequent reproducible milestones must include frozen candidate source and
constants, executable checks, terminal results, provenance and explicit limits.
Scientific conclusions must be distinguished from sampled tests, construction-only
results and incomplete searches. A checkpoint is considered externally saved only
after the expected-head, non-force update and a readback of the published bytes.
Research and publication have one coordinated writer; existing history is preserved.

The pinned upstream remains `andigu/uncompute` commit
`64b5a13aa249f1360846657392e6c66817b26d0f`. Source and license boundaries remain
those in the repository's `LICENSING.md` and `PROVENANCE.md`; this checkpoint does
not assign a new license to upstream or original contributions. No physical
hardware speedup, universal optimum or full-circuit proof is asserted.
