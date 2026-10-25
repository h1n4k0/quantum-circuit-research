#!/usr/bin/env python3
"""Independent resource/liveness census and source-bound review record.

Uses the upstream emitter, not a new simulator. The separately rerun package
checks retain their published bounded numerical/gate/component scope.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode=True
MANIFEST='aa7c6d1cdb089d87bd321ca2bcfe8cdb4a69a6c19f5dc5035affb5b125bf1580'
SOURCE='e3d39c6bbfa8b6a9b45cf082dcc8cac1f0139d4ffbb60387bf1e84125d087b5b'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,required=True)
    ap.add_argument('--replay',type=Path,required=True);ap.add_argument('--upstream',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists()
    assert sha(a.package/'MANIFEST.json')==MANIFEST
    manifest=json.loads((a.package/'MANIFEST.json').read_text())['sha256']
    assert all(sha(a.package/p)==h for p,h in manifest.items())
    source=a.package/'task/circuits/composed/circuit.py';assert sha(source)==SOURCE
    sys.path.insert(0,str(a.upstream.resolve()))
    from uncompute.testing import load_module
    mod=load_module(source.resolve(),'independent_coulomb_census',register=True)
    ops=list(mod.b.ops);census=Counter(o[0] for o in ops)
    # Count actual emitted primitives, independently of Builder.phase_summary.
    toffoli=census[6]+census[7]
    clifford=sum(census[k] for k in (3,4,5,8,9))
    live=set();peak=0;allocations=0
    for kind,value,position,total in mod.b.wire_log:
        if kind=='alloc':
            assert value not in live; live.add(value);allocations+=1
        elif kind=='free':
            assert value in live;live.remove(value)
        peak=max(peak,len(live))
    assert (toffoli,clifford,peak,len(ops))==(1097,7292,141,11172)
    assert live==set(sum(mod.RI,[])+sum(mod.RJ,[])+mod.KQ)
    summary=json.loads((a.replay/'summary.json').read_text())
    assert summary['status']=='PASS' and summary['frozen_package_unchanged']
    assert summary['metrics']['composed']['source_sha256']==SOURCE
    checks={name:json.loads((a.replay/(name+'.json')).read_text()) for name in ('strict','lookup','parity')}
    assert all(c['status']=='PASS' and c['candidate_sha256']==SOURCE for c in checks.values())
    assert checks['strict']['scope']['gate_level_cases']==837822
    assert checks['lookup']['actual_lookup']['addresses']==128
    assert checks['parity']['prefix_suffix_exact'] and checks['parity']['middle_gates']==7280
    report={'status':'PASS','reviewed_package_manifest_sha256':MANIFEST,'candidate_sha256':SOURCE,
      'reviewer_script_sha256':sha(Path(__file__)),
      'actual_expanded_ops_u64le_sha256':hashlib.sha256(b''.join(struct.pack('<9Q',*o) for o in ops)).hexdigest(),
      'independent_emitted_primitive_census':{'kinds':dict(census),'toffoli':toffoli,'benchmark_clifford':clifford,
        'expanded_operations':len(ops)},
      'independent_liveness_census':{'peak':peak,'allocation_events':allocations,
        'final_live_qubits':len(live),'only_persistent_io_live_at_end':True},
      'replayed_report_sha256':{n:sha(a.replay/n) for n in
        ('summary.json','strict.json','lookup.json','parity.json','composed_official/report.json')},
      'review_findings':[
        'Deterministic constructor reproduces the exact combined source from pinned surviving sources.',
        'Actual prefix and suffix match partial-cache source; the middle is alpha-equivalent including allocation lifetimes and classical outcome operands.',
        'Parity borrow/return are phase-free CX bridges under the stated norm-parity and baseline-restoration preconditions.',
        'All other magnitude/sign wires needed to return the alias are excluded from middle use.',
        'Fresh official tests, strict bounded witness tests, and complete lookup-interface tests passed.',
        'Standalone construction output guard was strengthened after review; no scientific source changed.'
      ],
      'limitations':'Independent read, resource census and fresh invocation; not an independent whole-circuit simulator. Strict gate evidence covers 837822 selected coordinate/accumulator cases, not the full task domain. Component transfer remains conditional on the baseline correctness/restoration contract. No hardware/global-optimum claim.'}
    assert sha(a.package/'MANIFEST.json')==MANIFEST
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
