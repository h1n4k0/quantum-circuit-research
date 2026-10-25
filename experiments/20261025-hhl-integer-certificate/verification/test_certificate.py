#!/usr/bin/env python3
"""Exact-rational spot checks, failure sensitivity, and runner guard tests.

This is not another full-domain simulator. It checks selected C records with
Python Fraction arithmetic and deliberately rejects corrupted numeric records.
"""
import argparse
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def exact_bracket(x):
    z=Fraction(32768,x); z2=z*z; term=z; total=z
    for n in range(1,32):
        # Independent exact rational coefficient recurrence, not generated.h.
        term*=Fraction((2*n-1)**2,2*n*(2*n+1))*z2
        total+=term
    return total,total+z**65/(1-z2)

def check_record(x,record):
    addend,lo,hi=record
    exact_lo,exact_hi=exact_bracket(x)
    assert Fraction(lo,1<<60)<=exact_lo<=exact_hi<=Fraction(hi,1<<60)
    assert max(abs(addend*(1<<28)-lo),abs(addend*(1<<28)-hi))<429*(1<<28)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--records',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); out=args.output.resolve()
    args.candidate=args.candidate.resolve();args.records=args.records.resolve()
    assert not out.exists(), 'output must not exist'
    for protected in (ROOT,args.candidate,args.records.parent):
        assert out!=protected and protected not in out.parents, 'output inside protected input'
    for ancestor in (out,*out.parents):
        assert not any((ancestor/name).exists() for name in
                       ('MANIFEST.json','PUBLICATION_MANIFEST.json')), 'output inside manifested input'
    out.mkdir(parents=True)
    constants=json.loads((args.candidate/'constants.json').read_text())
    points={65536,65537,2097150,2097151,1886892}
    for lo,bits in zip(constants['leaves']['lo'],constants['leaves']['bb']):
        points.update((lo,lo+(1<<bits)-1))
    rng=random.Random(20261025)
    points.update(rng.randrange(65536,2097152) for _ in range(512))
    records=args.records.read_bytes(); assert len(records)==2031616*24
    for x in sorted(points): check_record(x,struct.unpack_from('<QQQ',records,(x-65536)*24))
    witness=struct.unpack_from('<QQQ',records,(1886892-65536)*24)
    mutations={
        'collapsed_interval_rejected':(witness[0],witness[1],witness[1]),
        'bad_addend_rejected':(witness[0]+1000,witness[1],witness[2]),
    }
    rejected={}
    for name,record in mutations.items():
        try: check_record(1886892,record)
        except AssertionError: rejected[name]=True
        else: raise AssertionError('mutation survived: '+name)
    spec=importlib.util.spec_from_file_location('certificate_runner',ROOT/'reproduce.py')
    runner=importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    (out/'generated.h').write_text(runner.generate_header(constants))
    executable=out/'certify-ubsan'
    subprocess.run(['cc','-std=c11','-O1','-Wall','-Wextra','-Werror',
                    '-fsanitize=undefined','-fno-sanitize-recover=undefined',
                    '-I',str(out),str(ROOT/'verification/certify.c'),'-o',str(executable)],
                   capture_output=True,text=True,check=True)
    sanitized_records=out/'sanitized-records.bin'
    sanitized=subprocess.run([str(executable),str(sanitized_records)],
                             capture_output=True,text=True,check=True)
    assert not sanitized.stderr
    assert digest(sanitized_records)==digest(args.records)
    assert json.loads(sanitized.stdout)['status']=='PASS'
    bad=json.loads(json.dumps(constants)); bad['cfg']['RQ']+=1
    try: runner.generate_header(bad)
    except AssertionError: rejected['modified_datapath_config_rejected']=True
    else: raise AssertionError('config mutation survived')
    def run_guard(name,candidate,target):
        p=subprocess.run([sys.executable,'-B',str(ROOT/'reproduce.py'),
                          '--candidate',str(candidate),'--output',str(target)],
                         capture_output=True,text=True)
        assert p.returncode!=0,name
        (out/(name+'.log')).write_text(p.stdout+p.stderr)
        return True
    guard={}
    guard['existing_output_rejected']=run_guard('existing_output',args.candidate,out)
    for name,target in [('package_output',ROOT/'must-not-create'),
                        ('candidate_output',args.candidate/'must-not-create')]:
        assert not target.exists()
        guard[name+'_rejected']=run_guard(name,args.candidate,target)
        assert not target.exists()
    copied=out/'mutated-input'; copied.mkdir()
    shutil.copyfile(args.candidate/'constants.json',copied/'constants.json')
    (copied/'circuit.py').write_bytes((args.candidate/'circuit.py').read_bytes()+b'\n# deliberate test mutation\n')
    target=out/'must-not-create'
    guard['modified_source_rejected']=run_guard('modified_source',copied,target)
    assert not target.exists()
    # Exercise this test runner's own preflight, before it can mkdir or compile.
    test_targets={'self_package_output':ROOT/'must-not-create',
                  'self_candidate_output':args.candidate/'must-not-create'}
    for marker in ('MANIFEST.json','PUBLICATION_MANIFEST.json'):
        container=out/('frozen-'+marker);container.mkdir();(container/marker).write_text('{}\n')
        test_targets['self_'+marker+'_ancestor']=container/'must-not-create'
    for name,target in test_targets.items():
        assert not target.exists()
        p=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),
                          '--candidate',str(args.candidate),'--records',str(args.records),
                          '--output',str(target)],capture_output=True,text=True)
        assert p.returncode!=0 and not target.exists(),name
        guard[name+'_rejected']=True
    report={'status':'PASS','exact_rational_spot_checks':len(points),
            'spot_scope':'Every leaf endpoint, global endpoints, worst witness, 512 seeded draws with deduplication',
            'mutations':rejected,'guards':guard,'records_sha256':digest(args.records),
            'full_domain_undefined_behavior_sanitizer':{'status':'PASS','records_byte_identical':True,
                                                       'domain_values':2031616},
            'verifier_sha256':digest(Path(__file__)),
            'limits':'Spot checks independently verify fixed-point bounds, not the entire circuit or all-input arithmetic semantics.'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
