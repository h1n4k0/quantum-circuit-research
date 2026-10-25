#!/usr/bin/env python3
"""Offline replay of the composition, both baselines, and bounded certificates."""
import argparse
import hashlib
import importlib.util
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent
PIN = '64b5a13aa249f1360846657392e6c66817b26d0f'
SOURCE = 'e3d39c6bbfa8b6a9b45cf082dcc8cac1f0139d4ffbb60387bf1e84125d087b5b'
RAW = 'b8c6cdb00b03f0c22c657164bf9e19a5f06ed34ab42e7ea6a42f3a95c11f4792'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inventory():
    return {p.relative_to(ROOT).as_posix(): sha(p)
            for p in ROOT.rglob('*') if p.is_file()}

def check_manifest():
    assert not any(p.is_symlink() for p in ROOT.rglob('*')), 'Package contains symlinks'
    want = json.loads((ROOT / 'MANIFEST.json').read_text())['sha256']
    actual = inventory()
    del actual['MANIFEST.json']
    assert actual == want, 'Package manifest mismatch'

def validate_output(out, repo, up):
    assert not out.exists(), 'Output must be new'
    for root in (ROOT.parent, repo, up):
        assert out != root and root not in out.parents, 'Output within frozen inputs'
    for ancestor in (out, *out.parents):
        assert not any((ancestor / name).exists() for name in
                       ('MANIFEST.json', 'PUBLICATION_MANIFEST.json')), 'Output in manifested artifact'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repository', type=Path, required=True)
    ap.add_argument('--upstream', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    repo, up, out = args.repository.resolve(), args.upstream.resolve(), args.output.resolve()
    validate_output(out, repo, up)
    check_manifest()
    before = inventory()
    assert subprocess.check_output(['git', '-C', str(up), 'rev-parse', 'HEAD'], text=True).strip() == PIN
    assert subprocess.check_output(['git', '-C', str(up), 'status', '--porcelain', '--untracked-files=no'], text=True) == ''
    source = ROOT / 'task/circuits/composed/circuit.py'
    assert sha(source) == SOURCE
    raw = lzma.decompress((source.parent / 'circuit.ops.xz').read_bytes())
    assert hashlib.sha256(raw).hexdigest() == RAW
    for name in ('contract.json', 'grader.py', 'reference.py'):
        assert (ROOT / 'task' / name).read_bytes() == (up / 'tasks/coulomb-potential' / name).read_bytes()
    spec = importlib.util.spec_from_file_location('composition_recipe', ROOT / 'construction/compose.py')
    construction = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(construction)
    parity = repo / 'checkpoints/coulomb-parity-alias/task/circuits/norm_parity_alias_v1'
    cache = repo / 'checkpoints/coulomb-partial-cache/candidate'
    assert construction.compose((parity / 'circuit.py').read_bytes(), (cache / 'circuit.py').read_bytes()) == source.read_bytes()
    out.mkdir(parents=True)
    start = time.monotonic()
    task = out / 'task'
    task.mkdir()
    for name in ('contract.json', 'grader.py', 'reference.py'):
        shutil.copyfile(ROOT / 'task' / name, task / name)
    sources = {'composed': source.parent, 'partial_cache': cache, 'parity_alias': parity}
    env = os.environ.copy()
    env['PYTHONPATH'] = str(up)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    def run(name, command, emitted=None):
        process_env = env.copy()
        process_env.pop('UNCOMPUTE_OPS_PATH', None)
        if emitted is not None:
            process_env['UNCOMPUTE_OPS_PATH'] = str(emitted)
        with (out / (name + '.log')).open('w') as log:
            subprocess.run([sys.executable, '-B', *map(str, command)], env=process_env,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
    metrics = {}
    for name, directory in sources.items():
        staged = task / 'circuits' / name
        staged.mkdir(parents=True)
        for filename in ('circuit.py', 'meta.json'):
            shutil.copyfile(directory / filename, staged / filename)
        stream = out / (name + '.ops')
        run(name + '_emit', [staged / 'circuit.py'], stream)
        assert stream.read_bytes() == lzma.decompress((directory / 'circuit.ops.xz').read_bytes())
        run(name + '_official', [up / 'tools/eval.py', 'coulomb-potential', '--ops', stream, '--out', out / (name + '_official')])
        report = json.loads((out / (name + '_official/report.json')).read_text())
        assert report['verdict'] == 'OK'
        metrics[name] = {'source_sha256': sha(staged / 'circuit.py'), 'raw_sha256': sha(stream), **report['metrics']}
    candidate = task / 'circuits/composed/circuit.py'
    verification = ROOT / 'verification'
    run('parity', [verification / 'certify_composed_parity.py', candidate, '--baseline', task / 'circuits/partial_cache/circuit.py', '--upstream', up, '--output', out / 'parity.json'])
    run('lookup', [verification / 'certify_partial_cache_lookup.py', candidate, '--upstream', up, '--output', out / 'lookup.json'])
    run('strict', [verification / 'audit_coulomb_candidate.py', candidate, '--upstream', up, '--output', out / 'strict.json'])
    reports = {name: json.loads((out / (name + '.json')).read_text()) for name in ('parity', 'lookup', 'strict')}
    assert all(report['status'] == 'PASS' for report in reports.values())
    expected = {'composed': (1097, 141, 7292), 'partial_cache': (1097, 142, 7285), 'parity_alias': (1110, 141, 6723)}
    for name, values in expected.items():
        assert tuple(metrics[name][key] for key in ('toffoli', 'qubits', 'clifford')) == values
    assert reports['strict']['scope']['gate_level_cases'] == 837822
    assert reports['lookup']['allocator']['peak_live'] == 141
    assert reports['parity']['prefix_suffix_exact']
    assert inventory() == before, 'Frozen inputs changed during replay'
    result = {'status': 'PASS', 'upstream_commit': PIN, 'metrics': metrics,
              'construction_matches_exact_source': True, 'frozen_package_unchanged': True,
              'whole_circuit_scope': reports['strict']['scope'],
              'component_scope': 'Parity transfer and allocation-aware middle equivalence to partial-cache source; exact dirty-output lookup interface. Not all-coordinate/all-accumulator whole-circuit proof.',
              'wall_seconds': time.monotonic() - start}
    (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
