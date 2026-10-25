#!/usr/bin/env python3
"""Reproduce a rigorous, integer-only full-domain HHL numerical certificate.

The core certificate needs Python's standard library and a C compiler supporting
unsigned __int128. Optional comparison imports the unchanged upstream numerical
model only after the independent certificate has finished.
"""
import argparse
import array
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SOURCE_HASH = "d854ac76c46919b83568c307767049b241c19655b84330ba1cfd2b713df09f37"
CONSTANTS_HASH = "09e9d869cf54ec76361641aab0a83fa1122b2051ad383def3da16dae12e95370"
UPSTREAM_COMMIT = "64b5a13aa249f1360846657392e6c66817b26d0f"
CFG = {"NDN":15,"GUARD":4,"RPROD":11,"G1W":16,"TAU":3,"RQ":4,
       "G2W":5,"J0":2,"C0DROP":6,"QCAP":16,"PCAP":117,
       "B4":[4,5,5,5,6,6,6],"VORD":[2,1,0],"C0GL":11}
SCALE = 1 << 60

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check_manifest():
    manifest=json.loads((ROOT/"MANIFEST.json").read_text())["sha256"]
    actual={p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*')
            if p.is_file() and p!=ROOT/"MANIFEST.json"}
    assert not any(p.is_symlink() for p in ROOT.rglob('*')), "package symlink"
    assert actual==manifest, "package manifest mismatch"
    return actual

def coefficient_intervals():
    values = [Fraction(math.comb(2*n,n), 4**n*(2*n+1)) for n in range(32)]
    intervals = [(v.numerator*SCALE//v.denominator,
                  (v.numerator*SCALE+v.denominator-1)//v.denominator) for v in values]
    assert all(Fraction(lo,SCALE)<=v<=Fraction(hi,SCALE)
               for v,(lo,hi) in zip(values,intervals))
    assert Fraction(4,3*2**65) < Fraction(1,SCALE)
    return intervals

def generate_header(constants):
    assert constants["cfg"] == CFG, "unsupported datapath config"
    leaves = constants["leaves"]
    names = ("lo","bb","g0","g1","g2","sh")
    assert all(len(leaves[k])==345 for k in names)
    rows = list(zip(*(leaves[k] for k in names)))
    cursor = 65536
    for lo,bits,g0,g1,g2,shift in rows:
        assert lo==cursor and lo%(1<<bits)==0 and shift==15-bits
        cursor+=1<<bits
    assert cursor==2097152
    coeff=coefficient_intervals()
    text = "/* Generated exactly from pinned constants and rational coefficients. */\n"
    text += "struct Leaf { uint32_t lo,bits,g0,g1,g2,shift; };\n"
    text += "#define LEAF_COUNT 345\nstatic const struct Leaf LEAVES[LEAF_COUNT]={\n"
    text += "\n".join("{"+",".join(map(str,row))+"}," for row in rows)+"\n};\n"
    for index,name in enumerate(("COEF_LO","COEF_HI")):
        text += "static const uint64_t "+name+"[32]={"+",".join(
            "UINT64_C("+str(v[index])+")" for v in coeff)+"};\n"
    text += "static const unsigned PRODUCT_B4[7]={4,5,5,5,6,6,6};\n"
    return text

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate",type=Path,required=True,
                    help="Frozen hhl-octave-tensor/candidate directory")
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--upstream",type=Path,
                    help="Optional clean pinned checkout for shared-model comparison")
    ap.add_argument("--cc",default="cc")
    args=ap.parse_args()
    candidate=args.candidate.resolve(); output=args.output.resolve()
    assert not output.exists(), "output must not exist"
    protected=[ROOT,candidate]
    protected += [p for p in [ROOT,*ROOT.parents,candidate,*candidate.parents]
                  if (p/"MANIFEST.json").exists() or (p/"PUBLICATION_MANIFEST.json").exists()]
    if args.upstream:
        upstream=args.upstream.resolve(); protected.append(upstream)
        assert subprocess.check_output(["git","-C",str(upstream),"rev-parse","HEAD"],text=True).strip()==UPSTREAM_COMMIT
        assert not subprocess.check_output(["git","-C",str(upstream),"diff","--name-only","HEAD","--"],text=True).strip()
    assert all(p!=output and p not in output.parents for p in protected), "output is inside protected input"
    source=candidate/"circuit.py"; constants=candidate/"constants.json"
    assert sha(source)==SOURCE_HASH and sha(constants)==CONSTANTS_HASH, "frozen input pin mismatch"
    package_before=check_manifest()
    start=time.monotonic(); output.mkdir(parents=True)
    (output/"generated.h").write_text(generate_header(json.loads(constants.read_text())))
    executable=output/"certify"
    command=[args.cc,"-std=c11","-O2","-Wall","-Wextra","-Werror",
             "-I",str(output),str(ROOT/"verification/certify.c"),"-o",str(executable)]
    subprocess.run(command,check=True,capture_output=True,text=True)
    records=output/"certificate-records.bin"
    run=subprocess.run([str(executable),str(records)],check=True,capture_output=True,text=True)
    (output/"integer_certificate.json").write_text(run.stdout)
    integer=json.loads(run.stdout)
    assert integer["status"]=="PASS"
    assert records.stat().st_size==2031616*24
    max_f64_error=0; real_f64_disagreements=[]; addends=array.array("Q")
    for x,(delta,lo,hi) in enumerate(struct.iter_unpack("<QQQ",records.read_bytes()),65536):
        # This is a compatibility comparison, not part of the interval proof.
        f=math.asin(32768/x)*(1<<32)
        floor=math.floor(f); grader_ideal=floor+(f-floor>=0.5)
        rl=(lo+(1<<27))>>28; rh=(hi+(1<<27))>>28
        assert rl==rh, (x,"rounded real ideal not uniquely certified")
        if grader_ideal!=rl:
            real_f64_disagreements.append({"X":x,"f64_ideal":grader_ideal,"real_ideal":rl})
        max_f64_error=max(max_f64_error,abs(delta-grader_ideal))
        addends.append(delta)
    assert len(addends)==2031616 and max_f64_error<=429
    upstream_comparison=None
    if args.upstream:
        sys.path.insert(0,str(upstream))
        from uncompute.testing import load_module
        import numpy as np
        checks=load_module(upstream/"tasks/hhl-angle/circuits/discovered/checks.py",
                           "certificate_reference_comparison",register=True)
        expected,_=checks.certify_table(checks.CFG,((l.lo,l.bb,*l.coef) for l in checks.LEAVES))
        actual=np.asarray(addends,dtype=np.uint64)
        assert np.array_equal(expected,actual), "independent datapath differs from upstream model"
        upstream_comparison={"all_values_equal":True,"values":len(addends),
            "checks_sha256":sha(upstream/"tasks/hhl-angle/circuits/discovered/checks.py"),
            "scope":"Comparison only: the certificate does not import this model or its simulator."}
    assert sha(source)==SOURCE_HASH and sha(constants)==CONSTANTS_HASH
    assert check_manifest()==package_before, "package changed during replay"
    if args.upstream:
        assert subprocess.check_output(["git","-C",str(upstream),"rev-parse","HEAD"],text=True).strip()==UPSTREAM_COMMIT
        assert not subprocess.check_output(["git","-C",str(upstream),"diff","--name-only","HEAD","--"],text=True).strip()
    report={"status":"PASS","upstream_commit":UPSTREAM_COMMIT,
        "source_sha256":SOURCE_HASH,"constants_sha256":CONSTANTS_HASH,
        "method":"32-term positive arcsin series, Q60 integer directed bounds, rigorous global tail",
        "integer_certificate":integer,"max_pinned_f64_integer_error":max_f64_error,
        "rounded_real_vs_host_f64_disagreements":real_f64_disagreements,
        "upstream_model_comparison":upstream_comparison,
        "records_layout":"For X=65536..2097151, uint64 little-endian addend, asin_lower_Q60, asin_upper_Q60",
        "records_sha256":sha(records),"generated_header_sha256":sha(output/"generated.h"),
        "input_preservation":{"frozen_candidate_pins_unchanged":True,"complete_package_manifest_unchanged":True,
                              "upstream_tracked_files_unchanged":True if args.upstream else None},
        "verifier_sha256":sha(ROOT/"verification/certify.c"),"runner_sha256":sha(Path(__file__)),
        "environment":{"python":platform.python_version(),"machine":platform.machine(),
                       "compiler":subprocess.check_output([args.cc,"--version"],text=True).splitlines()[0]},
        "scope":"Full-domain numerical datapath certificate only, not a new gate-level all-accumulator theorem. Circuit linkage is the pinned source and prior/fresh sampled gate evidence. No hardware or optimum claim.",
        "seconds":time.monotonic()-start}
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
