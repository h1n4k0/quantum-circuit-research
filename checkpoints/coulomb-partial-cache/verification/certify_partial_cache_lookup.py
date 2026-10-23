#!/usr/bin/env python3
"""Exact actual-stream lookup certificate: all 128 addresses, symbolic dirty outputs,
and every independent HMR outcome. Restricted opcode/affine grammar fails closed.
No full-circuit numeric claim is made by this component checker.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
FULL=(1<<128)-1; NONE=(1<<64)-1

def check(ops,info,words):
    addr=info['address'];out=info['output'];assert len(addr)==7 and len(out)==24 and len(set(addr+out))==31
    state={q:(sum(((f>>j)&1)<<f for f in range(128)),0) for j,q in enumerate(addr)}
    state.update({q:(0,1<<j)for j,q in enumerate(out)})
    initial=state.copy();phase={};slots={};draws=0;count=0
    def get(q):return state.get(q,(0,0))
    def xor(a,b):return (a[0]^b[0],a[1]^b[1])
    def pure(q):
        x,s=get(q);assert s==0,('nonlinear dirty-output control',q);return x
    for index,op in enumerate(ops):
        kind,qa,qb,qt,ot,oc,rt,ct,cc=op
        assert rt==ct==cc==NONE
        if kind==0:
            assert qa==qb==ot==oc==NONE;state[qt]=xor(get(qt),(FULL,0))
        elif kind==3:
            assert qa==ot==oc==NONE and qb!=qt;state[qt]=xor(get(qt),get(qb))
        elif kind==6:
            assert ot==oc==NONE and len({qa,qb,qt})==3
            state[qt]=xor(get(qt),(pure(qa)&pure(qb),0));count+=1
        elif kind==9:
            assert qa==qb==oc==NONE and qt not in out+addr
            slots[ot]=1<<draws;phase[draws]=pure(qt);draws+=1;state[qt]=(0,0)
        elif kind==4:
            assert qa==ot==NONE and qb!=qt and oc!=NONE
            value=pure(qb)&pure(qt);cond=slots[oc]
            for d in range(draws):
                if cond>>d&1:phase[d]^=value
        elif kind==8:
            assert qa==qb==ot==oc==NONE;assert get(qt)==(0,0),('dirty reset',index,qt)
        else:raise AssertionError(('unsupported opcode',kind))
    for q in addr:assert get(q)==initial[q],('address',q)
    for j,q in enumerate(out):
        expected=sum(((words[f^info['logical_address_xor']]>>j)&1)<<f for f in range(128))
        assert get(q)==(expected,1<<j),('output',j)
    for q,v in state.items():
        if q not in addr+out:assert v==(0,0),('scratch',q)
    assert all(v==0 for v in phase.values()),'unrepaired measurement phase'
    return {'independent_hmr_draws':draws,'toffoli':count,'symbolic_dirty_outputs':24,'addresses':128,'operations':len(ops)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('candidate',type=Path);ap.add_argument('--upstream',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();assert not a.output.exists();sys.path.insert(0,str(a.upstream.resolve()))
    from uncompute.testing import load_module
    m=load_module(a.candidate.resolve(),'d_actual_cache_lookup_certificate',register=True)
    info=m.LOOKUP_PROOF;ops=list(m.b.ops);lo,hi=info['start'],info['end'];actual=ops[lo:hi]
    assert actual[0][0]==actual[-1][0]==0 and actual[0][3]==actual[-1][3]==info['address'][6]
    marks=[e for e in m.b.wire_log if e[0]=='mark' and e[1]=='qrom/setup'];assert len(marks)==1 and marks[0][2]==(lo,)
    words=[(m.G0f[f]-m.HBIT)|(m.SLf[f]<<m.GLOW)for f in range(128)]
    summary=check(actual,info,words)
    # Rebuild actual allocator boundary, not only a nominal scratch count.
    live=set();entry=None;peak=0;allocated=set()
    for e in m.b.wire_log:
        typ,q,pos,*_=e
        assert len(pos)==1
        if pos[0]<=lo and typ in ('alloc','free'):
            if typ=='alloc':assert q not in live;live.add(q)
            else:assert q in live;live.remove(q)
    entry=live.copy();peak=len(live)
    for e in m.b.wire_log:
        typ,q,pos,*_=e
        if lo<pos[0]<hi and typ in ('alloc','free'):
            if typ=='alloc':assert q not in live;live.add(q);allocated.add(q);peak=max(peak,len(live))
            else:assert q in live;live.remove(q)
    assert live==entry and allocated.isdisjoint(entry)
    assert set(info['address']+info['output'])<=entry
    accessed=set()
    for op in actual:
        for q in op[1:4]:
            if q!=NONE:accessed.add(q)
    assert accessed-entry<=allocated and accessed&entry<=set(info['address']+info['output'])
    # Every pre-existing scratch has an actual final R before this entry; minted
    # qubits have no previous quantum access and begin in the model's zero state.
    last={}
    for op in ops[:lo]:
        for q in op[1:4]:
            if q!=NONE:last[q]=op[0]
    assert all(q not in last or last[q]==8 for q in allocated)
    mutants=[]
    for kind in (3,4,6):
        rejected=False
        for i,op in enumerate(actual):
            if op[0]!=kind:continue
            try:check(actual[:i]+actual[i+1:],info,words)
            except (AssertionError,KeyError):mutants.append({'deleted_kind':kind,'index':i,'rejected':True});rejected=True;break
        assert rejected
    report={'status':'PASS','scope':'Actual captured entire qrom stage; all 128 physical addresses, all 2^24 dirty output words via explicitly checked affine-output grammar, all independent HMR records via symbolic ledger. Scratch clean at entry from allocator and previous reset checks. Does not prove complete-circuit approximation or all coordinate/accumulator cases.','candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'upstream_commit':'64b5a13aa249f1360846657392e6c66817b26d0f','expanded_lookup_u64le_sha256':hashlib.sha256(b''.join(struct.pack('<9Q',*op)for op in actual)).hexdigest(),'table_u32le_sha256':hashlib.sha256(b''.join(x.to_bytes(4,'little')for x in words)).hexdigest(),'actual_lookup':summary,'allocator':{'entry_live':len(entry),'peak_live':peak,'exit_live':len(live),'distinct_scratch_ids':len(allocated),'entry_and_exit_live_sets_equal':True,'preexisting_scratch_final_access_reset':True},'omission_mutants':mutants}
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
