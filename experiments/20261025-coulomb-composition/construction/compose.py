#!/usr/bin/env python3
"""Deterministically compose two preserved sources, without modifying either."""
import argparse
import hashlib
import json
from pathlib import Path

PARITY = 'bdbb62ac7537393aec212cb657aceeacdd5d15be3ebec9a5e30a456954cdccb4'
CACHE = '1379ef3398d3ac735bee2d4c4c4c045b77cce0500db506d91163a6fbfcc11cb7'

def compose(parity, cache):
    assert hashlib.sha256(parity).hexdigest() == PARITY
    assert hashlib.sha256(cache).hexdigest() == CACHE
    p, c = parity.decode(), cache.decode()
    begin = '        # Forward lookup via algebraic-normal-form monomial DFS.'
    end = '    # ---- 5. multiply:'
    assert p.count(begin) == 1 and p.count(end) == c.count(end) == 1
    a = c.index('PARTIAL_CACHE_PLAN = ')
    b = c.index('def build(', a)
    helpers = c[a:b]
    a = c.index('        global LOOKUP_PROOF')
    lookup = c[a:c.index(end, a)]
    p = p[:p.index(begin)] + lookup + p[p.index(end):]
    a = p.index('def build(')
    p = p[:a] + helpers + p[a:]
    old = 'The emitted circuit uses 1110 logical Toffoli gates and142 peak\nlogical qubits (TQ157620), versus the released1140/142 circuit.'
    new = ('This composition uses 1097 logical Toffoli gates and 141 peak\n'
           'logical qubits (TQ 154677), versus the released 1140/142 circuit.\n'
           'It composes the published norm-parity alias and partial-cache lookup;\n'
           'all unchanged arithmetic and numerical assumptions remain in force.')
    assert p.count(old) == 1
    return p.replace(old, new).encode()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repository', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    r, out = args.repository.resolve(), args.output.resolve()
    assert not out.exists(), 'Output must be new'
    for frozen in (r, Path(__file__).resolve().parents[1]):
        assert out != frozen and frozen not in out.parents, 'Output in input repository or package'
    for ancestor in (out, *out.parents):
        assert not any((ancestor / name).exists() for name in
                       ('MANIFEST.json', 'PUBLICATION_MANIFEST.json')), 'Output in frozen package'
    source = compose(
        (r / 'checkpoints/coulomb-parity-alias/task/circuits/norm_parity_alias_v1/circuit.py').read_bytes(),
        (r / 'checkpoints/coulomb-partial-cache/candidate/circuit.py').read_bytes())
    meta = json.loads((r / 'checkpoints/coulomb-parity-alias/task/circuits/norm_parity_alias_v1/meta.json').read_text())
    meta['expected'] = {'toffoli': 1097, 'qubits': 141}
    out.mkdir(parents=True)
    (out / 'circuit.py').write_bytes(source)
    (out / 'meta.json').write_text(json.dumps(meta, indent=2) + '\n')
    print(json.dumps({'source_sha256': hashlib.sha256(source).hexdigest(), 'expected': meta['expected']}))

if __name__ == '__main__':
    main()
