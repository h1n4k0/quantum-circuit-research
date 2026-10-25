#!/usr/bin/env python3
"""Finite exact-table screen of one invertible bit shear per HHL octave.
No circuit or resource claim follows until emitted-source verification.
"""
import argparse,functools,hashlib,itertools,json,multiprocessing,time
from pathlib import Path
import numpy as np

@functools.lru_cache(maxsize=100000)
def closure(masks):
 need={m for m in masks if m.bit_count()>1}
 stack=sorted(need,key=lambda x:(-x.bit_count(),x))
 for m in stack:
  if m.bit_count()<=2:continue
  parents=[m^(1<<i) for i in range(8) if m>>i&1]
  if not any(p in need for p in parents):
   p=max(parents,key=lambda p:(sum((z&p)==p for z in need),-p))
   need.add(p);stack.append(p)
 return tuple(sorted(need,key=lambda x:(x.bit_count(),x)))

def run(job):
 exponent,floor,raw,shear=job;n=exponent-floor;size=1<<n;ix=np.arange(size);best=None
 raw=np.array(raw,dtype=np.uint64)
 if shear:
  target,control=shear
  transformed=raw[ix^(((ix>>control)&1)<<target)]
 else:transformed=raw
 for pol in range(size):
  cf=transformed[ix^pol].copy()
  for i in range(n):
   v=cf.reshape(-1,1<<(i+1));v[:,1<<i:]^=v[:,:1<<i]
  nonzero=np.flatnonzero(cf).tolist()
  terms=[(m,int(cf[m])) for m in nonzero]
  for am in range(1,size-1):
   bm=(size-1)^am
   aset={m&am for m in nonzero if m&am};bset={m&bm for m in nonzero if m&bm}
   abank=aset|set(closure(tuple(sorted(aset))));bbank=closure(tuple(sorted(bset)))
   score=(len(abank)+len(bbank),len(terms),len(bbank),pol,am)
   if best is None or score<best[0]:
    best=(score,{'exponent':exponent,'floor':floor,'n':n,'shear':shear,'polarity':pol,
     'left_mask':am,'left_masks':sorted(abank,key=lambda x:(x.bit_count(),x)),
     'right_masks':list(bbank),'terms':terms,'phase_products':score[0]})
 q=best[1]
 for x,w in enumerate(raw):
  y=x
  if shear:
   target,control=shear;y^=((y>>control)&1)<<target
  y^=q['polarity'];got=0
  for m,z in q['terms']:
   if y&m==m:got^=z
  assert got==int(w),(exponent,shear,x)
 return q

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--constants',type=Path,required=True)
 ap.add_argument('--output',type=Path,required=True);ap.add_argument('--exponents',type=int,nargs='+',default=[18,19,20]);ap.add_argument('--jobs',type=int,default=4);a=ap.parse_args()
 output=a.output.resolve();constants=a.constants.resolve()
 assert not output.exists()
 for protected in (Path(__file__).resolve().parents[1],constants.parent):assert output!=protected and protected not in output.parents
 for ancestor in (output,*output.parents):assert not any((ancestor/name).exists() for name in ('MANIFEST.json','PUBLICATION_MANIFEST.json'))
 start=time.monotonic();c=json.loads(a.constants.read_text());g=c['cfg'];l=c['leaves'];truth=np.zeros(8192,dtype=np.uint64)
 for lo,bb,g0,g1,g2,sh in zip(*(l[k] for k in ('lo','bb','g0','g1','g2','sh'))):
  word=g2|(sh<<5)|((g1+4096)<<8)|((g0>>6)<<24)
  truth[lo>>8:(lo+(1<<bb))>>8]=word
 jobs=[]
 for e in a.exponents:
  floor=min(bb for lo,bb in zip(l['lo'],l['bb']) if 1<<e<=lo<1<<(e+1));n=e-floor
  raw=truth[(1<<e>>8)+(np.arange(1<<n)<<(floor-8))].tolist()
  for shear in [None]+[(t,c) for t in range(n) for c in range(n) if t!=c]:jobs.append((e,floor,raw,shear))
 results=[]
 with multiprocessing.Pool(a.jobs) as pool:
  for q in pool.imap_unordered(run,jobs):
   results.append(q)
   print(json.dumps({k:q[k] for k in ('exponent','shear','phase_products','polarity','left_mask')}),flush=True)
 byoct={e:sorted((q for q in results if q['exponent']==e),key=lambda q:(q['phase_products'],len(q['terms']),len(q['right_masks']),q['shear'] is not None,q['shear'] or [],q['polarity'],q['left_mask'])) for e in a.exponents}
 report={'status':'EXACT_TABLE_SCREEN_ONLY','constants_sha256':hashlib.sha256(a.constants.read_bytes()).hexdigest(),'best':[v[0] for v in byoct.values()], 'screens':[{k:q[k] for k in ('exponent','shear','phase_products','polarity','left_mask')} for q in sorted(results,key=lambda q:(q['exponent'],q['shear'] is not None,q['shear'] or []))], 'jobs':len(jobs),'seconds':time.monotonic()-start,'limitation':'Same deterministic greedy monomial-parent closure as prior plan; no global optimum or emitted resource count.'}
 a.output.write_text(json.dumps(report,indent=2)+'\n');print('BEST',[(e,qs[0]['phase_products'],qs[0]['shear']) for e,qs in byoct.items()],flush=True)
if __name__=='__main__':main()
