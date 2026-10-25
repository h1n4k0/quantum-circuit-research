#!/usr/bin/env python3
"""Independent exact-rational spot review of Q60 HHL arcsine enclosures.

Uses a direct 48-term sum, not the certificate's 32-term Q60 Horner scheme.
This checks selected interval records, not the full-domain C census again.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
import struct

SCALE = 1 << 60
COEFFICIENTS = [Fraction(math.comb(2*n, n), 4**n*(2*n+1)) for n in range(48)]

def bounds(x):
    z = Fraction(32768, x)
    assert 0 < z <= Fraction(1, 2)
    power = z
    total = Fraction(0)
    square = z*z
    for coefficient in COEFFICIENTS:
        assert 0 < coefficient <= 1
        total += coefficient * power
        power *= square
    # For every n, binom(2n,n)/4^n/(2n+1) <= 1. The entire omitted
    # positive tail is bounded by z^97/(1-z^2).
    return total, total + power/(1-square)

def check_interval(x, lo, hi):
    lower, upper = bounds(x)
    assert Fraction(lo, SCALE) <= lower <= upper <= Fraction(hi, SCALE), x

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--constants', required=True, type=Path)
    ap.add_argument('--records', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    output = args.output.resolve()
    assert not output.exists()
    for ancestor in (output, *output.parents):
        assert not any((ancestor / name).exists() for name in
                       ('MANIFEST.json', 'PUBLICATION_MANIFEST.json')), 'Output inside frozen artifact'
    constants = args.constants.read_bytes()
    assert hashlib.sha256(constants).hexdigest() == '09e9d869cf54ec76361641aab0a83fa1122b2051ad383def3da16dae12e95370'
    leaves = json.loads(constants)['leaves']
    points = {65536, 2097151, 1886892}
    for lo, width_bits in zip(leaves['lo'], leaves['bb']):
        points.update((lo, lo+(1 << width_bits)-1))
    rng = random.Random(20261025)
    points.update(rng.randrange(65536, 2097152) for _ in range(128))
    records = args.records.read_bytes()
    assert len(records) == 2031616*24
    for x in sorted(points):
        delta, lo, hi = struct.unpack_from('<QQQ', records, (x-65536)*24)
        assert delta < 1 << 32 and lo <= hi
        check_interval(x, lo, hi)
    x = 1886892
    delta, lo, hi = struct.unpack_from('<QQQ', records, (x-65536)*24)
    rejected = 0
    for mutated in ((lo+10**9, hi+10**9), (lo-10**9, hi-10**9)):
        try:
            check_interval(x, *mutated)
        except AssertionError:
            rejected += 1
    assert rejected == 2
    report = {'status': 'PASS', 'selected_inputs': len(points),
              'all_leaf_endpoints': True, 'deterministic_random_draws': 128,
              'method': 'Independent direct 48-term Fraction sum with exact geometric remainder bound, compared by rational inequalities to recorded Q60 intervals.',
              'shifted_interval_mutants_rejected': rejected,
              'records_sha256': hashlib.sha256(records).hexdigest(),
              'constants_sha256': hashlib.sha256(constants).hexdigest(),
              'checker_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'scope': 'Independent selected-input check of interval oracle only; not a second exhaustive census or circuit proof.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
