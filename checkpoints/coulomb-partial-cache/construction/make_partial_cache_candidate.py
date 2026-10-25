#!/usr/bin/env python3
"""Emit a new source copy; never edit the recovered baseline."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('plan',type=Path);p.add_argument('helper',type=Path);p.add_argument('target',type=Path);a=p.parse_args()
assert hashlib.sha256(a.baseline.read_bytes()).hexdigest()=='ce40b21cfc219816724dcf0ea47c03e0add6f685d6accd5871ff3685fe596b3f'
assert not a.target.exists();plan=json.loads(a.plan.read_text())['plan'];src=a.baseline.read_text()
start=src.index('        # Forward lookup via algebraic-normal-form monomial DFS.')
stop=src.index('    # ---- 5. multiply:',start)
src=src[:start]+'''        global LOOKUP_PROOF
        LOOKUP_PROOF = partial_cache_lookup(
            b, list(reversed(addr_bits)), sreg + slope,
            [(G0f[f] - HBIT) | (SLf[f] << GLOW) for f in range(128)],
            PARTIAL_CACHE_PLAN)

'''+src[stop:]
pos=src.index('def build(')
src=src[:pos]+'PARTIAL_CACHE_PLAN = '+repr(plan)+'\n\n'+a.helper.read_text()+'\n\n'+src[pos:]
a.target.mkdir(parents=True)
(a.target/'circuit.py').write_text(src)
meta=json.loads(a.baseline.with_name('meta.json').read_text());meta['expected']['toffoli']=1110-120+plan['toffoli']
(a.target/'meta.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps({'candidate_sha256':hashlib.sha256(src.encode()).hexdigest(),'expected':meta['expected']}))
