#!/usr/bin/env python3
"""Exact finite phase-table cancellation screen; gate emitter remains separate."""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from screen_phase_partition import table,closure

def main():
 p=argparse.ArgumentParser();p.add_argument('constants',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();t=time.monotonic();data=json.loads(a.constants.read_text());leaves=set(zip(data['leaves']['lo'],data['leaves']['bb']));truth=table(a.constants)
 def internal(lo,bb,floor):
  if (lo,bb) in leaves or bb-1<floor:return 0
  return 1+internal(lo,bb-1,floor)+internal(lo+(1<<(bb-1)),bb-1,floor)
 results=[]
 for floor in range(11,17):
  n=floor-8;size=1<<n;walk=3+sum(internal(1<<e,e,floor) for e in range(16,21))
  for pol in range(size):
   coeff=truth.reshape(-1,size)[:,np.arange(size)^pol].copy()
   for i in range(n):
    view=coeff.reshape(-1,1<<(i+1));view[:,1<<i:]^=view[:,:1<<i]
   masks=[int(m) for m in np.flatnonzero(np.bitwise_or.reduce(coeff,axis=0))]
   needed=closure(masks);results.append({'floor':floor,'polarity':pol,'walk_t':walk,'bank_t':len(needed),'phase_t':walk+len(needed),'required_masks':masks,'bank_masks':sorted(needed),'terms':int(np.count_nonzero(coeff))})
 results.sort(key=lambda r:(r['phase_t'],r['terms'],r['polarity']))
 out={'status':'EXACT_TABLE_SCREEN','constants_sha256':hashlib.sha256(a.constants.read_bytes()).hexdigest(),'configurations':len(results),'best':results[:10],'seconds':time.monotonic()-t,'scope':'ANF cancellation is exact. Bank closure is deterministic constructive, not optimal. Walk cost formula is checked only by actual emission later.'};a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
