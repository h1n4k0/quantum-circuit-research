"""Fixed-table 2+5 partial-cache QROM; dirty output XOR semantics.
Pure controls are restored before cache demolition. Output conjugations
implement CCX fanout without a clean product temporary.
"""
def partial_cache_lookup(b, address, output, words, plan):
    assert len(address)==7 and len(output)==24
    start=len(b.ops)
    b.x(address[6])  # source's physical flag is the complement of logical bit 6
    low_bits=plan['low_bits']; high_bits=plan['high_bits']
    coeff=plan['coefficients']
    # Source-local exact truth reconstruction: do not silently trust plan table.
    for f,w in enumerate(words):
        lo=sum(((f>>j)&1)<<i for i,j in enumerate(low_bits))
        hi=sum(((f>>j)&1)<<i for i,j in enumerate(high_bits))
        got=0
        for h in range(4):
            for l in range(32):
                if h&hi==h and l&lo==l:got^=coeff[h][l]
        assert got==w
    def fanout(q,word):
        for j,t in enumerate(output):
            if word>>j&1:b.cx(q,t)
    def product_fanout(a,c,word):
        assert word
        j=(word&-word).bit_length()-1;t=output[j]
        others=[q for k,q in enumerate(output)if k!=j and word>>k&1]
        for q in others:b.cx(t,q)
        b.ccx(a,c,t)
        for q in reversed(others):b.cx(t,q)
    low={1<<i:address[j]for i,j in enumerate(low_bits)};records=[]
    def compute(mask):
        for u in sorted(low):
            v=mask^u
            if u&mask==u and v and v in low:
                q=b.and_compute(low[u],low[v]);low[mask]=q
                rec=(mask,q,low[u],low[v]);records.append(rec);return rec
        raise AssertionError(('unavailable monomial',mask,sorted(low)))
    for mask in plan['cached_masks']:compute(mask)
    high={1:address[high_bits[0]],2:address[high_bits[1]]}
    high[3]=b.and_compute(high[1],high[2])
    for j,q in enumerate(output):
        if coeff[0][0]>>j&1:b.x(q)
    for h in range(1,4):fanout(high[h],coeff[h][0])
    for mask in plan['cached_low_features']:fanout(low[mask],coeff[0][mask])
    for h,terms in enumerate(plan['rank_products'],1):
        # Verify row factorization over the complete 24-output formal space.
        decoded=[0]*len(plan['cached_low_features'])
        for parity,word in terms:
            qs=[low[m]for j,m in enumerate(plan['cached_low_features'])if parity>>j&1]
            assert qs
            anchor=qs[0]
            for q in qs[1:]:b.cx(q,anchor)
            product_fanout(high[h],anchor,word)
            for q in reversed(qs[1:]):b.cx(q,anchor)
            for j in range(len(decoded)):
                if parity>>j&1:decoded[j]^=word
        assert decoded==[coeff[h][m]for m in plan['cached_low_features']]
    # All higher nodes have had their final product/readout use. Every streamed
    # degree<=4 monomial has two already-live pair/single factors. A retained
    # triple is needed only if quintic is streamed (not in this selected plan).
    retained=plan['retained_triple']
    released=[]
    for rec in reversed(records):
        mask,q,u,v=rec
        if mask.bit_count()>2 and mask!=retained:
            b.and_release(q,u,v);del low[mask];released.append(mask)
    records=[r for r in records if r[0]not in released]
    for mask in plan['streamed_masks']:
        rec=compute(mask);_,q,u,v=rec
        fanout(q,coeff[0][mask])
        for h in range(1,4):product_fanout(high[h],q,coeff[h][mask])
        b.and_release(q,u,v);del low[mask];assert records.pop()==rec
    b.and_release(high[3],high[1],high[2])
    for mask,q,u,v in reversed(records):b.and_release(q,u,v)
    b.x(address[6])
    return {'start':start,'end':len(b.ops),'address':list(address),'output':list(output),'logical_address_xor':64}
