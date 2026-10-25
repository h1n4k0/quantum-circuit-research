#!/usr/bin/env python3
"""Finite exploratory screen; exact coefficient-table ANF, not a gate result."""
import argparse,json,itertools,hashlib,time
from pathlib import Path
import numpy as np

def table(path):
 c=json.loads(path.read_text());g=c['cfg'];l=c['leaves'];a=np.zeros(8192,dtype=np.uint64)
 for lo,bb,g0,g1,g2,sh in zip(*(l[k] for k in ('lo','bb','g0','g1','g2','sh'))):
  w=g2 | (sh<<g['G2W']) | ((g1+(1<<g['QCAP']>>g['GUARD']))<<(g['G2W']+3)) | ((g0>>g['C0DROP'])<<(g['G2W']+3+g['G1W']))
  a[lo>>8:(lo+(1<<bb))>>8]=w
 return a

def anf(a):
 a=a.copy()
 for i in range(13):
  block=1<<(i+1);a.reshape(-1,block)[:,1<<i:]^=a.reshape(-1,block)[:,:1<<i]
 return a

def closure(masks):
 need={m for m in masks if m.bit_count()>1}
 for m in sorted(need,key=lambda x:(-x.bit_count(),x)):
  pass
 stack=sorted(need,key=lambda x:(-x.bit_count(),x))
 for m in stack:
  if m.bit_count()<=2:continue
  pp=[m^(1<<i) for i in range(13) if m>>i&1]
  if not any(p in need for p in pp):
   p=max(pp,key=lambda p:(sum((z&p)==p for z in need),-p));need.add(p);stack.append(p)
 return need

def main():
 p=argparse.ArgumentParser();p.add_argument('constants',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();t=time.monotonic();truth=table(a.constants);coeff=anf(truth)
 assert np.array_equal(anf(coeff),truth)
 terms=[int(i) for i in np.flatnonzero(coeff)];best=[]
 for n in range(3,8):
  for bits in itertools.combinations(range(13),n):
   left=sum(1<<b for b in bits);right=8191^left
   l=closure(m&left for m in terms);r=closure(m&right for m in terms)
   best.append({'left':list(bits),'left_bank':len(l),'right_bank':len(r),'and_features':len(l)+len(r)})
 best.sort(key=lambda r:(r['and_features'],max(r['left_bank'],r['right_bank'])))
 out={'status':'SCREEN_ONLY','constants_sha256':hashlib.sha256(a.constants.read_bytes()).hexdigest(),'invalid_selectors':'zero extension on addresses 0..255; no physical contract there','nonzero_anf_terms':len(terms),'partitions':len(best),'best':best[:30],'seconds':time.monotonic()-t}
 a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
