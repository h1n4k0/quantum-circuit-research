#!/usr/bin/env python3
"""Independent audit runner; never edits candidate or upstream.

Checks structural change scope, full-domain arithmetic via the published
datapath certificate, and adversarial gate-level lanes with the simulator's
algebraic (all measurement outcomes) cleanliness ledger.
"""
import argparse
import ast
import contextlib
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import time

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fast_write(sim, wires, vals):
    vals = np.asarray(vals, dtype=np.uint64)
    for i, wire in enumerate(wires):
        sim._grow(sim.qubits, wire)
        sim.qubits[wire] = int.from_bytes(np.packbits((vals >> i) & 1, bitorder="little").tobytes(), "little")


def fast_read(sim, wires):
    vals = np.zeros(sim.batch, dtype=np.uint64)
    for i, wire in enumerate(wires):
        raw = sim._q(wire).to_bytes((sim.batch + 7) // 8, "little")
        bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="little")[:sim.batch].astype(np.uint64)
        vals |= bits << i
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--upstream", type=Path, default=Path(__file__).resolve().parents[1] / "upstream")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    t0 = time.monotonic()
    sys.path.insert(0, str(args.upstream))
    from uncompute import Simulator
    from uncompute.testing import load_module

    base = args.upstream / "tasks/hhl-angle/circuits/discovered"
    cand = args.candidate.resolve()
    assert sha(base / "constants.json") == sha(cand.parent / "constants.json"), "arithmetic constants changed"
    marker = "    # ---- 9."
    def normalized_prefix(path):
        tree = ast.parse(path.read_text().split(marker)[0])
        tree.body = [node for node in tree.body if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str))]
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                node.names = [alias for alias in node.names if alias.name != "assert_metrics"]
        return ast.dump(tree, include_attributes=False)
    assert normalized_prefix(base / "circuit.py") == normalized_prefix(cand), "pre-fixup executable code changed"
    mod = load_module(cand, "audit_candidate", register=True)
    builder, regs = mod.build()
    checks = load_module(base / "checks.py", "audit_published_checks", register=True)
    addend, true_error = checks.certify_table(checks.CFG, ((lf.lo, lf.bb, *lf.coef) for lf in checks.LEAVES))

    # Every leaf-selector equivalence class at the minimum dyadic granularity,
    # plus lower-bit endpoints and midpoint. Three accumulator carry regimes.
    # Phase decoder depends on X[8:] only; arithmetic/output k is adversarial.
    minbit = min(lf.bb for lf in mod.LEAVES)
    assert minbit == 8
    xs = []
    ks = []
    modulus = 1 << 33
    for block in range(65536, 2097152, 1 << minbit):
        for low in (0, 127, 255):
            x = block + low
            delta = int(addend[x - 65536])
            for k in (0, modulus - 1, (modulus - delta) % modulus):
                xs.append(x)
                ks.append(k)
    xs = np.asarray(xs, dtype=np.uint64)
    ks = np.asarray(ks, dtype=np.uint64)
    worst_integer = 0
    total = len(xs)
    for start in range(0, total, 8192):
        x = xs[start:start + 8192]
        k = ks[start:start + 8192]
        sim = Simulator(builder, batch=len(x), seed=20261021, strict=True)
        fast_write(sim, regs["X"], x)
        fast_write(sim, regs["k"], k)
        sim.run()
        sim.assert_clean()
        assert np.array_equal(fast_read(sim, regs["X"]), x)
        got = fast_read(sim, regs["k"])
        want = (k + addend[(x - 65536).astype(np.int64)].astype(np.uint64)) % modulus
        assert np.array_equal(got, want), (start, "candidate differs from exact published arithmetic model")
        assert sim.stats.toffoli // len(x) == builder.phase_summary()["total_emitted_toffoli"]
    # Independent scalar f64 rounding (not np.rint) over all input values.
    ideal = np.floor(checks.FF + 0.5).astype(np.int64)
    error = ((addend - ideal + (1 << 32)) % modulus) - (1 << 32)
    worst_integer = int(np.max(np.abs(error)))
    report = {
        "status": "PASS",
        "candidate": cand.parent.name + "/" + cand.name,
        "candidate_sha256": sha(cand),
        "constants_sha256": sha(cand.parent / "constants.json"),
        "upstream_commit": "64b5a13aa249f1360846657392e6c66817b26d0f",
        "scope": {
            "pre_fixup_executable_ast_identical": True,
            "constants_identical": True,
            "full_arithmetic_domain_values": len(addend),
            "gate_level_cases": total,
            "distinct_decoder_input_classes": 7936,
            "measurement_outcomes": "all, via affine per-draw ledger on tested inputs",
            "accumulators": ["zero", "all ones", "exact output wrap seam"],
            "not_proved": "Not an exhaustive gate-level test over all 2^33 accumulator values; simulator and arithmetic model are upstream implementations."
        },
        "metrics": {"toffoli": builder.phase_summary()["total_emitted_toffoli"], "peak_logical_qubits": builder.peak_qubits},
        "max_error_integer_units": worst_integer,
        "max_error_unrounded_units": true_error,
        "max_error_radians": true_error / (1 << 32),
        "wall_seconds": time.monotonic() - t0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
