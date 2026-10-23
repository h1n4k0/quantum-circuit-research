# Fixed-table partial-cache Coulomb lookup

This is a **new candidate from the recovered initial-001 source**, not a restoration of any later lost experiment. Its source, table, raw stream, finite search, component checker, and replay scripts are included.

| Circuit | Logical Toffoli | Peak logical qubits | TQ | Benchmark Clifford |
|---|---:|---:|---:|---:|
| Recovered combined_v1 | 1110 | 142 | 157620 | 6716 |
| Partial-cache19 v1 | **1097** | **142** | **155774** | **7285** |

The tradeoff is **13 fewer Toffoli and 569 more benchmark Clifford gates**, not an improvement in every metric or a hardware speedup. The numerical table, arithmetic, and 15-AND inverse lookup are unchanged. The new forward lookup costs 107 instead of 120 Toffoli. Source SHA256: `1379ef3398d3ac735bee2d4c4c4c045b77cce0500db506d91163a6fbfcc11cb7`.

## Construction and scope

Use address bits 1,2,3,4,5 as the low five and bits 0,6 as the high two. Cache all ten low pairs and nine higher low monomials, together with the one high pair. Three independent output-coefficient matrix factorizations cost 19,21,19 products. A dirty-output CNOT conjugation applies each product to its entire output mask without another clean wire. Release the higher cache after its final use, then stream the seven omitted low monomials and their three high products.

The total is `19 + 1 + (19+21+19) + 7*(1+3) = 107`. Actual allocator replay confirms 122 live qubits at entry, peak 142, and the same 122 live set at exit. This does not presume that discarded monomials remain available.

`construction/search_partial_cache.py` scans all 240,240 configurations of this **specific** family: 21 coordinate 2+5 splits and all ten low pairs plus nine of sixteen higher monomials. Its minimum score is 107 (22 configurations). This is not a general lookup, circuit, or quantum lower bound. Other encodings, mixed factors, output donation, feedback, or temporal schedules are outside that scan.

## Evidence

- The exact actual lookup stream is checked over all 128 physical addresses and **all 24 arbitrary dirty output bits**. A fail-closed opcode grammar guarantees affine dependence on these dirty bits; coefficient masks prove the full `2^24` domain, not sampled values. A symbolic per-HMR ledger verifies all 27 independent measurement results. Scratch entry/exit and actual allocator events are checked. Removing a relevant CX, CZ, or CCX is rejected.
- The original independent integer-oracle audit is rerun: 195,075 positive norms for the integer model, 139,637 attainable norms, and **837,822 gate-level cases** (one magnitude witness per norm, both signs, three accumulator cases). Its strict measurement ledger covers all outcomes **for those tested basis inputs**.
- The official stored-stream evaluator passes 9,019 live sampled shots with zero output, phase/sign, or dirty-qubit failures.
- The integer error remains at most 32; the original true-error bound is `32.5 / 2^24 < 2e-6`.

**Not proved:** all coordinate pairs and all accumulator values for the complete circuit. The component's exhaustive symbolic statement must not be promoted into an exhaustive whole-circuit statement. “Toffoli” means the benchmark logical primitive, not a physical T-gate count. Outcome-ID count is not peak classical storage.

## Reproduce offline

Use Python with the pinned upstream environment (NumPy and the upstream kernel build). No network operation is performed by the runner. The upstream checkout must be exactly `andigu/uncompute` commit `64b5a13aa249f1360846657392e6c66817b26d0f`, with tracked files unchanged.

```sh
PYTHONDONTWRITEBYTECODE=1 python reproduce.py \
  --upstream /path/to/uncompute \
  --output /path/to/new-external-output
```

The runner stages an exact candidate copy under a fresh task tree, re-emits and matches the raw stream hash, reruns the component and 837,822-case audit, and evaluates the stream. It rejects existing output paths, output anywhere in the publication container/upstream, and manifested ancestors. It checks that all package files remain unchanged. Search replay is optional and separate; the runner does not claim to rerun discovery.

## Provenance and licensing

The baseline is the published `initial-001/candidates/coulomb/combined_v1/circuit.py`, SHA256 `ce40b21cfc219816724dcf0ea47c03e0add6f685d6accd5871ff3685fe596b3f`. Candidate modification is restricted to the forward QROM block plus the embedded helper/plan and metadata pin. Historical source comments about the previous “certified stream” describe their inherited code, not byte identity of the new full circuit.

The two `audit_*` files are unchanged copies of the recovered initial-001 verification scripts. The source derives from the Apache-2.0 upstream; its license is included. Consult the repository's `LICENSING.md` for the original snapshot's licensing scope; this checkpoint does not introduce a blanket license over unrelated contributions.
