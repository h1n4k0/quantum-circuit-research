#!/usr/bin/env python3
"""Complete finite cache scan: 2+5 coordinate split; all ten low pairs plus nine other monomials.
Scores a specific clean-cache/direct-output construction, not general optimality.
"""
import argparse,hashlib,itertools,json,time
from pathlib import Path

def factor(vectors):
    piv={}; generators=[]; representations=[]
    for original in vectors:
        x=original; tag=0
        while x:
            p=x.bit_length()-1
            if p in piv:
                row,rt=piv[p]; x^=row;tag^=rt
            else:
                j=len(generators);generators.append(original);piv[p]=(x,tag^(1<<j));tag=1<<j;break
        representations.append(tag)
    for x,tag in zip(vectors,representations):
        y=0
        for j,g in enumerate(generators):
            if tag>>j&1:y^=g
        assert x==y
    parities=[sum(((t>>j)&1)<<i for i,t in enumerate(representations)) for j in range(len(generators))]
    return list(zip(parities,generators))

def rank(xs):
    p={}
    for x in xs:
        while x:
            i=x.bit_length()-1
            if i in p:x^=p[i]
            else:p[i]=x;break
    return len(p)

def main():
    p=argparse.ArgumentParser();p.add_argument('profile',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    inp=json.loads(a.profile.read_text());w=inp['words'];an=w[:]
    for j in range(7):
        for m in range(128):
            if m>>j&1:an[m]^=an[m^(1<<j)]
    pairs=[m for m in range(1,32) if m.bit_count()==2];higher=[m for m in range(1,32) if m.bit_count()>2];singles=[1<<j for j in range(5)]
    best=None;hist={};count=0;t0=time.monotonic()
    for low in itertools.combinations(range(7),5):
        high=tuple(j for j in range(7)if j not in low)
        def mask(v,bits):return sum(((v>>i)&1)<<j for i,j in enumerate(bits))
        coeff=[[an[mask(h,high)|mask(l,low)]for l in range(32)]for h in range(4)]
        for extra in itertools.combinations(higher,9):
            cached=sorted(pairs+list(extra),key=lambda x:(x.bit_count(),x));lm=singles+cached
            ranks=[rank([coeff[h][l]for l in lm])for h in range(1,4)]
            cost=19+1+sum(ranks)+7*4
            hist[cost]=hist.get(cost,0)+1;count+=1
            key=(cost,low,tuple(cached))
            if best is None or key<best[0]:best=(key,{'low_bits':low,'high_bits':high,'cached_masks':cached,'ranks':ranks,'coefficients':coeff})
    plan=best[1];lm=singles+plan['cached_masks'];plan['cached_low_features']=lm
    plan['rank_products']=[factor([plan['coefficients'][h][l]for l in lm])for h in range(1,4)]
    plan['streamed_masks']=[l for l in range(1,32)if l not in lm]
    # After cached products, release all higher cache nodes except a triple used by quintic stream.
    triples=[m for m in plan['cached_masks'] if m.bit_count()==3]
    plan['retained_triple']=triples[0] if 31 in plan['streamed_masks'] else None
    plan['toffoli']=best[0][0];plan['max_additional_workspace']=20
    out={'status':'PASS','scope':'Exact finite scan of 21 coordinate 2+5 splits, all ten low pairs and nine of sixteen higher monomials. Cost assumes direct dirty-output product fanout and early higher-cache release. Emission/occupancy not yet proved; not global lookup optimality.','profile_sha256':hashlib.sha256(a.profile.read_bytes()).hexdigest(),'candidate_sha256':inp['candidate_sha256'],'table_u32le_sha256':inp['table_u32le_sha256'],'configurations':count,'cost_histogram':hist,'plan':plan,'wall_seconds':time.monotonic()-t0}
    a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='plan'},indent=2));print('PLAN',json.dumps(plan))
if __name__=='__main__':main()
