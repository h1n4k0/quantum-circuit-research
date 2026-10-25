#!/usr/bin/env python3
"""Exact ANF/cofactor-rank profile of the unmodified initial Coulomb table.
This is an algebraic cost screen, not a circuit resource or optimality claim.
"""
import argparse, hashlib, itertools, json, sys
from pathlib import Path

def rank(xs):
    rows={}
    for x in xs:
        while x:
            p=x.bit_length()-1
            if p in rows: x ^= rows[p]
            else: rows[p]=x; break
    return len(rows)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('candidate',type=Path); ap.add_argument('--upstream',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    assert not a.output.exists(); sys.path.insert(0,str(a.upstream.resolve()))
    from uncompute.testing import load_module
    m=load_module(a.candidate.resolve(),'d_coulomb_table_profile',register=True)
    words=[(m.G0f[f]-m.HBIT)|(m.SLf[f]<<m.GLOW) for f in range(128)]
    anf=words[:]
    for j in range(7):
        for s in range(128):
            if s>>j&1: anf[s]^=anf[s^(1<<j)]
    for f,w in enumerate(words):
        v=0
        for s,c in enumerate(anf):
            if s&f==s:v^=c
        assert v==w
    rows=[]
    for k in range(1,7):
        for low in itertools.combinations(range(7),k):
            high=[j for j in range(7) if j not in low]
            def mask(v,bits):return sum(((v>>i)&1)<<j for i,j in enumerate(bits))
            ranks=[rank([anf[mask(h,high)|mask(l,low)] for l in range(1,1<<k)]) for h in range(1,1<<len(high))]
            # Fully precomputed non-linear pure-side monomials; one mixed product per row-space generator.
            pure=(1<<k)-k-1+(1<<len(high))-len(high)-1
            rows.append({'low_bits':list(low),'high_bits':high,'ranks':ranks,'pure_bank_ands':pure,'mixed_ands':sum(ranks),'total_ands':pure+sum(ranks)})
    rows.sort(key=lambda r:(r['total_ands'],r['low_bits']))
    out={'status':'PASS','scope':'Fixed table, coordinate address splits, fully computed pure monomial banks, separate high-monomial controls and low-parity rank factorization. This omits workspace and emission and is not a lower bound.','candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),'upstream_commit':'64b5a13aa249f1360846657392e6c66817b26d0f','word_bits':m.GLOW+m.SW,'table_u32le_sha256':hashlib.sha256(b''.join(w.to_bytes(4,'little')for w in words)).hexdigest(),'words':words,'nonzero_nonlinear_anf':sum(bool(v)and i.bit_count()>1 for i,v in enumerate(anf)),'rows':rows}
    a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in('words','rows')},indent=2));print('BEST',json.dumps(rows[:3]))
if __name__=='__main__':main()
