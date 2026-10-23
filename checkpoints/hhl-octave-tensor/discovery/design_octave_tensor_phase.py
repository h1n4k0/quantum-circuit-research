#!/usr/bin/env python3
"""Construct exact per-octave packed ANF plans and a phase-only candidate.

No numerical coefficients or arithmetic prefix are changed. Planning minimizes
this finite split-monomial construction's feature count, not arbitrary circuits.
"""
import argparse,itertools,json,hashlib,shutil,time
from pathlib import Path
import numpy as np
from screen_phase_partition import table,closure

def plan(constants):
 c=json.loads(constants.read_text());truth=table(constants);ls=c['leaves'];plans=[]
 for e in range(16,21):
  floor=min(bb for lo,bb in zip(ls['lo'],ls['bb']) if 1<<e<=lo<1<<(e+1));n=e-floor;size=1<<n
  raw=truth[(1<<e>>8)+(np.arange(size)<<(floor-8))];best=None
  for pol in range(size):
   cf=raw[np.arange(size)^pol].copy()
   for i in range(n):
    v=cf.reshape(-1,1<<(i+1));v[:,1<<i:]^=v[:,:1<<i]
   terms=[(m,int(w)) for m,w in enumerate(cf) if w]
   for na in range(1,n):
    for aa in itertools.combinations(range(n),na):
     am=sum(1<<i for i in aa);bm=(size-1)^am
     aset={m&am for m,w in terms if m&am};bset={m&bm for m,w in terms if m&bm}
     abank=aset|closure(aset);bbank=closure(bset)
     score=(len(abank)+len(bbank),len(terms),len(bbank),pol,am)
     if best is None or score<best[0]:best=(score,{'exponent':e,'floor':floor,'n':n,'polarity':pol,'left_mask':am,'left_masks':sorted(abank,key=lambda x:(x.bit_count(),x)),'right_masks':sorted(bbank,key=lambda x:(x.bit_count(),x)),'terms':terms,'phase_products':score[0]})
  q=best[1]
  # Independent direct polynomial evaluation at every local address.
  for x,w in enumerate(raw):
   y=x^q['polarity'];got=0
   for m,z in q['terms']:
    if y&m==m:got^=z
   assert got==int(w),(e,x)
  plans.append(q)
 return plans

SUFFIX='''    # ---- 9. Per-octave split-monomial phase repair ----
    # Tensor plans are exact ANFs of the unchanged packed coefficient table.
    # The left bank includes the octave flag; right monomials are unconditioned.
    # Every left node is consumed and HMR-uncomputed before its parent, while
    # right controls remain live. This is a timed construction, not a span count.
    plans = json.loads((pathlib.Path(__file__).parent / "phase_plan.json").read_text())["plans"]
    measurements = list(mb_g2) + list(mb_sh) + list(mb_g1) + list(mb_c0)

    def repair_octave(ctrl, e):
        p = plans[e - 16]
        floor, n, pol = p["floor"], p["n"], p["polarity"]
        for i in range(n):
            if pol >> i & 1:
                b.x(XQ[floor + i])
        right = {1 << i: XQ[floor + i] for i in range(n) if not (p["left_mask"] >> i & 1)}
        parents = {}
        for mask in p["right_masks"]:
            bit = next(1 << i for i in range(n) if mask >> i & 1 and mask ^ (1 << i) in right)
            parent = mask ^ bit
            right[mask] = b.and_compute(right[parent], right[bit])
            parents[mask] = (parent, bit)
        child = {mask: [] for mask in [0] + p["left_masks"]}
        for mask in p["left_masks"]:
            bit = next(1 << i for i in range(n) if mask >> i & 1 and mask ^ (1 << i) in child)
            child[mask ^ bit].append((mask, bit))
        readout = {mask: [] for mask in child}
        for mask, word in p["terms"]:
            readout[mask & p["left_mask"]].append((mask & ~p["left_mask"], word))
        def visit(mask, wire):
            for rm, word in readout[mask]:
                selected = [measurements[i] for i in range(len(measurements)) if word >> i & 1]
                parity = selected[0]
                for outcome in selected[1:]:
                    parity = parity ^ outcome
                if rm:
                    b.cz(wire, right[rm], cond=parity)
                else:
                    b.z(wire, cond=parity)
            for cm, bit in child[mask]:
                raw = XQ[floor + bit.bit_length() - 1]
                anc = b.and_compute(wire, raw)
                visit(cm, anc)
                b.and_release(anc, wire, raw)
        with b.phase(f"fixup/tensor_oct{e - 16}"):
            visit(0, ctrl)
        for mask in reversed(p["right_masks"]):
            parent, bit = parents[mask]
            b.and_release(right[mask], right[parent], right[bit])
        for i in range(n):
            if pol >> i & 1:
                b.x(XQ[floor + i])

    def octave_walk(e, ctrl=None):
        q = XQ[e]
        if e == 16:
            repair_octave(ctrl, 16)
        elif ctrl is None:
            b.x(q)
            octave_walk(e - 1, q)
            b.x(q)
            repair_octave(q, e)
        else:
            a = b.and_compute(ctrl, q, pol=(True, False))
            octave_walk(e - 1, a)
            b.cx(ctrl, a)
            repair_octave(a, e)
            b.and_release(a, ctrl, q)
    with b.phase("fixup/octave_walk"):
        octave_walk(20)
    return b, _r
'''

def main():
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--destination',type=Path,required=True);a=ap.parse_args();t=time.monotonic();assert not a.destination.exists();ps=plan(a.source.parent/'constants.json');shutil.copytree(a.source.parent,a.destination);s=a.source.read_text();prefix=s.split('    # ---- 9.')[0];ending=s[s.index('\n\n# ------------------------------------------------------------------ entry'):];(a.destination/'circuit.py').write_text(prefix+SUFFIX+ending)
 report={'status':'EXACT_LOCAL_TABLES','construction':'per-octave split-monomial phase readout','plans':ps,'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'constants_sha256':hashlib.sha256((a.source.parent/'constants.json').read_bytes()).hexdigest(),'planned_phase_products':3+sum(p['phase_products'] for p in ps),'seconds':time.monotonic()-t};(a.destination/'phase_plan.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='plans'},indent=2));print([(p['exponent'],p['floor'],p['phase_products'],p['polarity'],p['left_mask']) for p in ps])
if __name__=='__main__':main()
