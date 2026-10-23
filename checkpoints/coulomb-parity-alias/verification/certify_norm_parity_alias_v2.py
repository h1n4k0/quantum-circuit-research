#!/usr/bin/env python3
"""Actual-stream parity bridge and allocation-aware middle alpha equivalence.

This certifies the changed interface, not the baseline's full task correctness.
No timing, phase, or gate operand is inferred from source comments.
"""
import argparse, hashlib, itertools, json, sys
from pathlib import Path
NONE=(1<<64)-1

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ensure_new_output(p):
    p=p.resolve()
    if p.exists():raise ValueError('Output must be new')
    for a in (p.parent,*p.parents):
        if any((a/m).exists() for m in ('MANIFEST.json','PUBLICATION_MANIFEST.json')):
            raise ValueError('Output is inside a manifested checkpoint')
    return p

def event_cut(b,name):
    hits=[i for i,e in enumerate(b.wire_log) if e[0]=='mark' and e[1]==name]
    # mirror() restores its surrounding phase at exit, yielding a second
    # un-squarer mark. The first is its actual entry; other cuts are unique.
    assert len(hits)==1 or (name=='un-squarer' and len(hits)==2),(name,hits)
    i=hits[0];return i,b.wire_log[i][2][0]

def live_at(b,event_index):
    live=set()
    for k,v,pos,n in b.wire_log[:event_index]:
        if k=='alloc':assert v not in live;live.add(v)
        if k=='free':assert v in live;live.remove(v)
    return live

def canonical_middle(b,start_name,end_name,norm0):
    start,p=event_cut(b,start_name);stop,q=event_cut(b,end_name)
    lives=live_at(b,start)
    rename={x:('persistent',x) for x in lives};rename[norm0]=('norm0',)
    events={}
    for kind,v,pos,n in b.wire_log[start:stop]:
        if kind in ('alloc','free'):
            assert len(pos)==1
            events.setdefault(pos[0],[]).append((kind,v))
    out=[];serial=0
    for i in range(p,q+1):
        for k,w in events.get(i,[]):
            if k=='alloc':
                assert w not in rename
                rename[w]=('temporary',serial);serial+=1
                out.append(('alloc',rename[w]))
            else:
                assert w in rename
                out.append(('free',rename.pop(w)))
        if i<q:
            op=list(b.ops[i])
            for j in (1,2,3):
                if op[j]!=NONE:op[j]=rename[op[j]]
            out.append(('gate',tuple(op)))
    return out,serial,(p,q),set(rename.values())

def scalar(ops,state):
    state=state.copy()
    for op in ops:
        k,a,b,t,ot,oc,rt,ct,cc=op
        assert oc==cc==NONE
        if k==3:state[t]=state.get(t,0)^state.get(b,0)
        elif k==8:
            assert state.get(t,0)==0,'nonzero RESET'
            state[t]=0
        else:raise AssertionError(('unexpected bridge op',k))
    return state

def main():
    ap=argparse.ArgumentParser();ap.add_argument('candidate',type=Path)
    ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--upstream',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    output=ensure_new_output(args.output)
    sys.path.insert(0,str(args.upstream.resolve()))
    from uncompute.testing import load_module
    base=load_module(args.baseline.resolve(),'parity_base',register=True)
    cand=load_module(args.candidate.resolve(),'parity_cand',register=True)
    assert sha(args.baseline)=='ce40b21cfc219816724dcf0ea47c03e0add6f685d6accd5871ff3685fe596b3f'
    tr=cand.b.parity_alias_trace
    old=tr['norm_before'][0];a,b,c=tr['magnitude_lsb'];assert len({old,a,b,c})==4
    assert tuple(tr['norm_middle'])==(a,)+tuple(tr['norm_before'][1:])
    baseline_start=event_cut(base.b,'normalize/setup')[1]
    assert baseline_start==tr['square_end']
    assert list(base.b.ops[:baseline_start])==list(cand.b.ops[:tr['square_end']])
    baseline_end=event_cut(base.b,'un-squarer')[1]
    assert list(base.b.ops[baseline_end:])==list(cand.b.ops[tr['return_end']:])
    cb,nb,rb,lb=canonical_middle(base.b,'normalize/setup','un-squarer',old)
    cc,nc,rc,lc=canonical_middle(cand.b,'normalize/setup','norm-parity/return',a)
    assert cb==cc,'Actual middle differs beyond live-wire alpha renaming'
    assert lb-lc=={('persistent',a)} and not lc-lb
    assert nb==nc
    # Every other coordinate/sign input stays untouched throughout the middle.
    forbidden=set(sum(cand.RI,[])+sum(cand.RJ,[]))-{a}
    forbidden |= set(range(73,76))
    for op in cand.b.ops[rc[0]:rc[1]]:
        assert not (set(op[1:4]) & forbidden)
    borrow=list(cand.b.ops[tr['square_end']:tr['middle_begin']])
    giveback=list(cand.b.ops[tr['middle_end']:tr['return_end']])
    assert [o[0] for o in borrow]==[3,3,3,8]
    assert [o[0] for o in giveback]==[3,3,3]
    for bits in itertools.product((0,1),repeat=3):
        start={a:bits[0],b:bits[1],c:bits[2],old:sum(bits)%2}
        mid=scalar(borrow,start)
        assert mid=={a:sum(bits)%2,b:bits[1],c:bits[2],old:0}
        assert scalar(giveback,mid)==start
    omitted=0
    for side,ops in [('borrow',borrow),('return',giveback)]:
        for j,op in enumerate(ops):
            if op[0]==8:continue  # deleting a known-zero reset is semantically neutral
            caught=False
            for bits in itertools.product((0,1),repeat=3):
                start={a:bits[0],b:bits[1],c:bits[2],old:sum(bits)%2}
                try:
                    mid=scalar(borrow[:j]+borrow[j+1:] if side=='borrow' else borrow,start)
                    end=scalar(giveback[:j]+giveback[j+1:] if side=='return' else giveback,mid)
                    if end!=start:caught=True
                except AssertionError:caught=True
            assert caught;omitted+=1
    # Exact backwards data dependency cone for actual square's lowest bit.
    sq=event_cut(base.b,'squarer/a0g1')[1]
    needed={old};selected=[]
    for i in reversed(range(sq,baseline_start)):
        op=base.b.ops[i];k,x,y,t=op[:4]
        if k in (0,3,6) and t in needed:
            selected.append((i,op))
            if k in (3,6):needed.add(y)
            if k==6:needed.add(x)
        elif k==5 and (y in needed or t in needed):
            selected.append((i,op));needed.update((y,t))
        elif k in (8,9) and t in needed:
            selected.append((i,op));needed.remove(t)
    selected.reverse();assert needed=={old,a,b,c}
    assert all(o[0]==3 and o[3]==old and o[2] in (a,b,c) for _,o in selected)
    for bits in itertools.product((0,1),repeat=3):
        start={a:bits[0],b:bits[1],c:bits[2],old:0}
        assert scalar([o for _,o in selected],start)[old]==sum(bits)%2
    # The norm bit's initial zero is a fresh/reclaimed clean allocation at this cut.
    allocs=[e for e in base.b.wire_log if e[0]=='alloc' and e[1]==old and e[2][0]<=sq]
    assert allocs and allocs[-1][2][0]==sq
    report={'status':'PASS','candidate_sha256':sha(args.candidate),'baseline_sha256':sha(args.baseline),
      'checker_sha256':sha(Path(__file__)),'upstream_commit':'64b5a13aa249f1360846657392e6c66817b26d0f',
      'actual_trace':tr,'borrow_ops':borrow,'return_ops':giveback,
      'square_parity_dependency_ops':[i for i,_ in selected],
      'square_parity_all_inputs':'Exact backwards dependency cone: seven CX, only three magnitude LSBs and initial clean norm0',
      'bridge_cases':8,'nonneutral_omission_mutants_rejected':omitted,
      'middle_gates':rb[1]-rb[0],'matched_temporary_allocations':nb,
      'canonical_middle_sha256':hashlib.sha256(repr(cb).encode()).hexdigest(),
      'prefix_suffix_exact':True,'protected_middle_inputs':sorted(forbidden),
      'scope':'Exact interface change and allocation-aware middle alpha-equivalence. Baseline task correctness is not established by this certificate; full task tests remain the separately reported 837822 witness cases.'}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','middle_gates','matched_temporary_allocations','bridge_cases','nonneutral_omission_mutants_rejected')}))
if __name__=='__main__':main()
