# Recovered HHL initial-001: fresh reproduction

This checkpoint only reproduces the publicly recoverable circuit. It does not recover, inherit, or validate any later unavailable candidate.

| Circuit | Toffoli | Peak logical Q | TQ | Benchmark Clifford census |
|---|---:|---:|---:|---:|
| Released upstream | 1348 | 115 | 155020 | 56419 |
| Public initial-001 | 1273 | 115 | 146395 | 14889 |

The new emitted initial-001 stream is byte-identical to its published compressed stream, SHA-256 `b6041c74cdbee72641967a11fb54318d4776204c84785942133f6e6698c64eea`. Source and stored-stream official tests both pass (8702 shots); the released source passes 8741 shots. The unchanged public audit passes all 2,031,616 numerical-model inputs and 71,424 gate cases covering every 7,936 selector class and three accumulator regimes. Its strict affine ledger checks all measurement outcomes on each tested input. This is **not** a proof over all 2^33 accumulators; the simulator and numerical model are upstream implementations. The float-based reported maximum is 9.9452798663e-8 radians, not a new directed-rounding certificate.

## Reproduce

Use Python 3.10+ with NumPy and Click. Obtain the separate upstream repository at `64b5a13aa249f1360846657392e6c66817b26d0f`. Optionally run `make -C upstream kernel` using a local C compiler. No LLM API is used.

```sh
python reproduce.py --upstream /path/to/upstream \
  --snapshot /path/to/quantum-circuit-research/initial-001 \
  --output /path/to/new-output-directory
```

The output directory must not exist and must be outside both inputs. The runner copies the task into fresh output, replays both official modes and the published strict audit, verifies unchanged input hashes, and binds all result files and raw streams. `environment.json` records this run's dependency versions. Timing is environment-specific and not a hardware speedup.

The candidate, constants, stored stream and inherited audit source remain in the repository's original `initial-001/`. Upstream attribution and licensing scope are unchanged; see the repository root licensing and provenance documents.

## Version 2 guard hardening

Scientific result files are unchanged from the fresh version-1 reproduction. This runner additionally pins the published audit, rejects modified tracked upstream files, and rejects output inside its package or any containing manifest-frozen ancestor. The new guard tests are not a new gate-domain proof.
