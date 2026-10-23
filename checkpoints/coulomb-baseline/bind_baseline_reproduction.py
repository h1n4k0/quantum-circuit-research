#!/usr/bin/env python3
"""Bind a fresh Coulomb baseline replay to the recovered public checkpoint.

This verifies existing reports and stream identity; it does not rerun the
simulator and is not a full-coordinate or arbitrary-accumulator theorem.
"""
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", type=Path, required=True)
    ap.add_argument("--upstream", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    snapshot = a.snapshot.resolve()
    work = a.work.resolve()
    pin = "64b5a13aa249f1360846657392e6c66817b26d0f"
    head = subprocess.check_output(["git", "-C", str(a.upstream), "rev-parse", "HEAD"], text=True).strip()
    assert head == pin
    assert not subprocess.check_output(["git", "-C", str(a.upstream), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    pub = json.loads((snapshot / "PUBLICATION_MANIFEST.json").read_text())
    for rel, digest in pub["files"].items():
        assert sha(snapshot / rel) == digest, rel
    old = snapshot / "initial-001/candidates/coulomb/combined_v1"
    new = work / "task/circuits/baseline"
    for name in ("circuit.py", "meta.json", "circuit.ops.xz"):
        assert (old / name).read_bytes() == (new / name).read_bytes()
    for name in ("grader.py", "contract.json", "reference.py"):
        assert (work / "task" / name).read_bytes() == (a.upstream / "tasks/coulomb-potential" / name).read_bytes()
    emitted = work / "results/baseline_emitted.ops"
    assert emitted.read_bytes() == lzma.decompress((old / "circuit.ops.xz").read_bytes())
    official_path = work / "results/baseline_official/report.json"
    independent_path = work / "results/baseline_independent.json"
    official = json.loads(official_path.read_text())
    independent = json.loads(independent_path.read_text())
    assert official["verdict"] == "OK" and all(v == 0 for v in official["counters"].values())
    assert official["h_ops"] == sha(emitted)
    assert (official["metrics"]["toffoli"], official["metrics"]["qubits"]) == (1110, 142)
    assert independent["status"] == "PASS" and independent["candidate_sha256"] == sha(new / "circuit.py")
    assert independent["scope"]["gate_level_cases"] == 837822
    assert independent["scope"]["attainable_squared_distances"] == 139637
    assert independent["max_integer_error_attainable"] == 32
    report = {
        "status": "PASS", "kind": "fresh-reproduction-binding", "upstream_commit": head,
        "public_checkpoint": "initial-001", "public_manifest_sha256": sha(snapshot / "PUBLICATION_MANIFEST.json"),
        "verified_manifest_payloads": len(pub["files"]),
        "source_sha256": sha(new / "circuit.py"), "meta_sha256": sha(new / "meta.json"),
        "compressed_ops_sha256": sha(new / "circuit.ops.xz"), "expanded_ops_sha256": sha(emitted),
        "fresh_emission_byte_identical_to_published_stream": True,
        "official_report_sha256": sha(official_path), "independent_report_sha256": sha(independent_path),
        "metrics": official["metrics"], "scope": independent["scope"],
        "limitation": "No claim over all coordinate pairs or all 2^25 accumulators; strict all-outcome checking is on the stated basis-input cases. Simulator and official evaluator are unchanged upstream code.",
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
