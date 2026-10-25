#!/usr/bin/env python3
"""Independent exact integer oracle and full-distance strict gate audit.

The oracle rounds C/sqrt(n) using only integer comparisons, independently
of the upstream floating-point sqrt oracle. Every attainable norm-squared
is represented in gate-level tests, with both coordinate orientations and
three adversarial initial accumulators. This is not all 2^48 coordinate
pairs nor all 2^25 accumulator values.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

from audit_hhl_candidate import fast_read, fast_write, sha


def exact_rounded_inverse_root(n, c=1 << 24):
    # q=floor(C/sqrt(n)); round upward iff C/sqrt(n)>=q+1/2.
    q = math.isqrt(c*c // n)
    cmp = 4*c*c - n*(2*q+1)**2
    assert cmp != 0, (n, "unexpected exact half tie")
    return q + (cmp > 0)


def witnesses():
    w = np.full((195076, 3), -1, dtype=np.int16)
    for x in range(256):
        for y in range(x, 256):
            z = np.arange(y, 256, dtype=np.int32)
            ns = x*x + y*y + z*z
            w[ns, 0] = x
            w[ns, 1] = y
            w[ns, 2] = z
    valid = np.where(w[:, 0] >= 0)[0]
    valid = valid[valid != 0]
    assert len(valid) == 139637
    return valid, w[valid].astype(np.uint64)


def model(n, mod):
    if n < 4:
        return (mod.QV[n] << 5) + (1 << 23)
    e = n.bit_length() - 1
    m = n << (17-e)
    f = ((e & 1) << 6) | ((m >> 11) & 63)
    r = (m >> 5) & 63
    s, g = mod.SLf[f], mod.G0f[f]
    p = sum((s << i) >> 2 for i in range(6) if (r >> i) & 1)
    v = (g-p) << (8-(e >> 1))
    return (v >> 2) + ((v >> 1) & 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--upstream", type=Path, default=Path(__file__).resolve().parents[1]/"upstream")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    start = time.monotonic()
    sys.path.insert(0, str(args.upstream))
    from uncompute import Simulator
    from uncompute.testing import load_module
    cand = args.candidate.resolve()
    mod = load_module(cand, "audit_coulomb_candidate", register=True)
    builder, ri, rj, kq = mod.b, mod.RI, mod.RJ, mod.KQ
    valid, coords = witnesses()
    exact = [0] + [exact_rounded_inverse_root(n) for n in range(1,195076)]
    ref_mismatches = [n for n in range(1,195076) if exact[n] != round((1 << 24)/math.sqrt(n))]
    assert not ref_mismatches
    norm_digest = hashlib.sha256(valid.astype("<u4").tobytes()).hexdigest()
    oracle_digest = hashlib.sha256(np.asarray(exact,dtype="<u4")[valid].tobytes()).hexdigest()
    assert norm_digest == "f52f7e1b110369374daea81136a21c36eca11364ccb2653b725d4f6ba6b1e8cc"
    assert oracle_digest == "3de8b2b0b3063d0f46aa4cbcf528173b73d4cf0d28d0a2fac27491238d804439"
    values = np.asarray([model(n,mod) for n in range(1,195076)],dtype=np.int64)
    integer_err = values - np.asarray(exact[1:])
    assert max(abs(integer_err)) <= 32
    errors = integer_err[valid-1]
    deltas = values[valid-1].astype(np.uint64)
    # Six cases per attainable norm: opposite coordinate signs and k0/max/seam.
    total = len(valid)*6
    modulus = 1 << 25
    max_gate_error = 0
    for lo in range(0,total,8192):
        idx = np.arange(lo,min(lo+8192,total))
        witness_id, variant = idx//6, idx%6
        invert = variant >= 3
        d = deltas[witness_id]
        kval = np.choose(variant%3,[np.zeros(len(idx),dtype=np.uint64), np.full(len(idx),modulus-1,dtype=np.uint64),(modulus-d)%modulus])
        xyz = coords[witness_id]
        left = np.where(invert[:,None],xyz,0)
        right = np.where(invert[:,None],0,xyz)
        sim = Simulator(builder,batch=len(idx),seed=20261021,strict=True)
        for c in range(3):
            fast_write(sim,ri[c],left[:,c])
            fast_write(sim,rj[c],right[:,c])
        fast_write(sim,kq,kval)
        sim.run()
        sim.assert_clean()
        for c in range(3):
            assert np.array_equal(fast_read(sim,ri[c]),left[:,c])
            assert np.array_equal(fast_read(sim,rj[c]),right[:,c])
        got = fast_read(sim,kq)
        assert np.array_equal(got,(kval+d)%modulus), (lo,"integer model mismatch")
        assert sim.stats.toffoli//len(idx) == builder.phase_summary()["total_emitted_toffoli"]
    report = {
        "status":"PASS",
        "candidate":cand.parent.name + "/" + cand.name,
        "candidate_sha256":sha(cand),
        "upstream_commit":"64b5a13aa249f1360846657392e6c66817b26d0f",
        "scope":{
            "exact_oracle_domain_values":195075,
            "attainable_squared_distances":len(valid),
            "gate_level_cases":total,
            "coordinate_witnesses":"one magnitude triple per attainable squared distance, both signs",
            "accumulators":["zero","all ones","exact output wrap seam"],
            "measurement_outcomes":"all via affine per-draw ledger on tested inputs",
            "not_proved":"Not all coordinate pairs or accumulator values; circuit semantics are upstream strict Simulator, independently selected tests and exact integer oracle."
        },
        "metrics":{"toffoli":builder.phase_summary()["total_emitted_toffoli"],"peak_logical_qubits":builder.peak_qubits},
        "oracle_matches_float_all_values":True,
        "domain_sha256":norm_digest,
        "oracle_sha256":oracle_digest,
        "max_integer_error_attainable":int(np.max(np.abs(errors))),
        "max_integer_error_all_positive_values":int(np.max(np.abs(integer_err))),
        "true_error_upper_bound":32.5/(1<<24),
        "true_error_requirement":2e-6,
        "boundary_norms":[int(n) for n,e in zip(valid,errors) if abs(e)==32],
        "wall_seconds":time.monotonic()-start,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
