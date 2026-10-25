#!/usr/bin/env python3
"""Independent finite-table, resource, and frame-mutation review of HHL shear."""
import argparse
import bisect
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
SOURCE = 'fc37886611a9245bab10d454ac4a07d538a534c28b3bdcbceeefda9211c3b1e7'
PIN = '64b5a13aa249f1360846657392e6c66817b26d0f'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--package', type=Path, required=True)
    ap.add_argument('--replay', type=Path, required=True)
    ap.add_argument('--upstream', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    package, replay, up, out = (getattr(args, k).resolve() for k in ('package', 'replay', 'upstream', 'output'))
    assert not out.exists()
    for p in (package, replay, up):
        assert out != p and p not in out.parents
    for p in (out, *out.parents):
        assert not any((p/n).exists() for n in ('MANIFEST.json', 'PUBLICATION_MANIFEST.json'))
    manifest = sha(package/'MANIFEST.json')
    frozen = json.loads((package/'MANIFEST.json').read_text())['sha256']
    assert {p.relative_to(package).as_posix(): sha(p) for p in package.rglob('*')
            if p.is_file() and p != package/'MANIFEST.json'} == frozen
    assert not any(p.is_symlink() for p in package.rglob('*'))
    assert subprocess.check_output(['git', '-C', str(up), 'rev-parse', 'HEAD'], text=True).strip() == PIN
    assert not subprocess.check_output(['git', '-C', str(up), 'status', '--porcelain', '--untracked-files=no'], text=True).strip()
    candidate = package/'task/circuits/shear'
    assert sha(candidate/'circuit.py') == SOURCE
    constants = json.loads((candidate/'constants.json').read_text())['leaves']
    plans = json.loads((candidate/'phase_plan.json').read_text())
    assert plans['changes'] == [{'exponent': 18, 'before': 12, 'after': 11, 'shear': [1, 5]}]
    # Independent direct truth-table evaluation, without the discovery module.
    classes = 0
    for x in range(65536, 1 << 21, 256):
        j = bisect.bisect_right(constants['lo'], x)-1
        expected = (constants['g2'][j] | (constants['sh'][j] << 5)
                    | ((constants['g1'][j]+4096) << 8) | ((constants['g0'][j] >> 6) << 24))
        p = plans['plans'][x.bit_length()-1-16]
        y = (x >> p['floor']) & ((1 << p['n'])-1)
        if p.get('shear'):
            target, control = p['shear']
            y ^= ((y >> control) & 1) << target
        y ^= p['polarity']
        actual = 0
        for mask, word in p['terms']:
            if y & mask == mask:
                actual ^= word
        assert actual == expected, x
        classes += 1
    assert classes == 7936
    sys.path.insert(0, str(up))
    from uncompute.testing import load_module
    module = load_module(candidate/'circuit.py', 'independent_shear_resources', register=True)
    builder, registers = module.build()
    ops = list(builder.ops)
    census = Counter(op[0] for op in ops)
    toffoli = census[6]+census[7]
    clifford = sum(census[k] for k in (3, 4, 5, 8, 9))
    live = set()
    peak = 0
    for kind, q, position, total in builder.wire_log:
        if kind == 'alloc':
            assert q not in live
            live.add(q)
        elif kind == 'free':
            assert q in live
            live.remove(q)
        peak = max(peak, len(live))
    assert (toffoli, clifford, peak, len(ops)) == (1205, 13601, 115, 28588)
    assert live == set(registers['X']+registers['k']) and len(live) == 54
    summary = json.loads((replay/'summary.json').read_text())
    assert summary['status'] == 'PASS' and summary['source_sha256'] == SOURCE
    assert all(sha(replay/name) == h for name, h in summary['evidence_sha256'].items())
    for name in ('strict.json', 'suffix.json', 'numeric_transfer.json'):
        assert json.loads((replay/name).read_text())['status'] == 'PASS'
    out.mkdir(parents=True)
    task = out/'task'
    task.mkdir()
    for name in ('contract.json', 'grader.py', 'reference.py'):
        shutil.copyfile(package/'task'/name, task/name)
    text = (candidate/'circuit.py').read_text()
    line = '            b.cx(XQ[floor + control], XQ[floor + target])'
    assert text.count(line) == 2
    mutations = []
    for index in range(2):
        parts = text.split(line)
        parts[index] += '            pass  # deliberate missing frame CX'
        mutant = parts[0] + (line if index != 0 else '') + parts[1] + (line if index != 1 else '') + parts[2]
        directory = task/'circuits'/('omit_frame_'+str(index))
        directory.mkdir(parents=True)
        for name in ('constants.json', 'phase_plan.json'):
            shutil.copyfile(candidate/name, directory/name)
        (directory/'circuit.py').write_text(mutant)
        result = subprocess.run([sys.executable, '-B', str(package/'verification/verify_octave_suffix.py'),
                                 str(directory/'circuit.py'), '--upstream', str(up), '--output', str(out/('mutant_'+str(index)+'.json'))],
                                capture_output=True, text=True)
        assert result.returncode != 0 and 'AssertionError' in result.stderr
        assert 'SyntaxError' not in result.stderr and 'ImportError' not in result.stderr
        expected_failure = ('assert not constant and not any(ledger)' if index == 0
                            else 'assert all(q.get(w,0)==initial.get(w,0)')
        assert expected_failure in result.stderr, 'Mutation failed for an unexpected reason'
        (out/('mutant_'+str(index)+'.log')).write_text(result.stdout+result.stderr)
        mutations.append({'omitted_frame': 'enter' if index == 0 else 'exit',
                          'suffix_checker_rejected': True,
                          'failure_stage': 'phase ledger' if index == 0 else 'wire restoration'})
    assert sha(package/'MANIFEST.json') == manifest
    assert all(sha(package/p) == h for p, h in frozen.items())
    assert subprocess.check_output(['git', '-C', str(up), 'rev-parse', 'HEAD'], text=True).strip() == PIN
    assert not subprocess.check_output(['git', '-C', str(up), 'status', '--porcelain', '--untracked-files=no'], text=True).strip()
    report = {'status': 'PASS', 'package_manifest_sha256': manifest, 'source_sha256': SOURCE,
              'reviewer_sha256': sha(Path(__file__)), 'exact_polynomial_selector_classes': classes,
              'independent_emitted_census': {'toffoli': toffoli, 'benchmark_clifford': clifford,
                                             'peak_qubits': peak, 'expanded_operations': len(ops),
                                             'final_persistent_io_qubits': len(live)},
              'expanded_ops_u64le_sha256': hashlib.sha256(b''.join(struct.pack('<9Q', *o) for o in ops)).hexdigest(),
              'frame_mutations': mutations,
              'replay_report_sha256': {name: sha(replay/name) for name in
                  ('summary.json', 'candidate/report.json', 'baseline/report.json', 'released/report.json', 'stored/report.json', 'strict.json', 'suffix.json', 'numeric_transfer.json', 'numeric/report.json')},
              'limits': 'Independent finite truth-table check, resource/liveness census, and frame-mutation sensitivity, plus fresh invocation of existing verification. No independent all-input/all-accumulator whole-circuit simulator or global optimality proof.'}
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
