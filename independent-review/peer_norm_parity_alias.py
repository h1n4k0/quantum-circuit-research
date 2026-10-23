#!/usr/bin/env python3
"""Actual-record parity-alias peer, without the author's allocation-log canonicalizer.

The middle is compared by a rolling injective wire renaming. R/HMR zero its
quantum target, so its physical name may be independently reused. The verifier
retains every classical/outcome field and never executes a simulator.
"""
import argparse,contextlib,hashlib,io,itertools,json,struct,subprocess,sys,types
from pathlib import Path
NO=2**64-1
BASE='ce40b21cfc219816724dcf0ea47c03e0add6f685d6accd5871ff3685fe596b3f'
UP='64b5a13aa249f1360846657392e6c66817b26d0f'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def scalar(ops,s):
 s=s.copy()
 for op in ops:
  k,qa,qb,qt,ot,oc,rt,ct,cc=op
  assert qa==ot==oc==rt==ct==cc==NO
  if k==3:s[qt]=s.get(qt,0)^s.get(qb,0)
  elif k==8:assert qb==NO and s.get(qt,0)==0
  else:raise AssertionError('bridge grammar')
 return s

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['baseline','candidate','upstream','output']:p.add_argument('--'+name,type=Path,required=True)
 z=p.parse_args();out=z.output.resolve();assert not out.exists()
 for source in [z.baseline,z.candidate,Path(__file__)]:
  for parent in source.resolve().parents:
   if (parent/'MANIFEST.json').exists() or (parent/'PUBLICATION_MANIFEST.json').exists():assert not(out==parent or parent in out.parents)
 assert sha(z.baseline)==BASE
 assert subprocess.check_output(['git','-C',str(z.upstream),'rev-parse','HEAD'],text=True).strip()==UP
 assert not subprocess.check_output(['git','-C',str(z.upstream),'diff','--name-only','HEAD','--'],text=True).strip()
 before=[sha(z.baseline),sha(z.candidate)]
 sys.path.insert(0,str(z.upstream.resolve()));from uncompute.testing import load_module
 with contextlib.redirect_stdout(io.StringIO()):
  old=load_module(z.baseline.resolve(),'parity_peer_old',register=True)
  new=load_module(z.candidate.resolve(),'parity_peer_new',register=True)
 a=list(old.b.ops);b=list(new.b.ops);t=new.b.parity_alias_trace
 s=t['square_end'];lo=t['middle_begin'];hi=t['middle_end'];ret=t['return_end'];end=hi-(lo-s)
 assert len(a)+7==len(b) and lo-s==4 and ret-hi==3
 assert a[:s]==b[:s] and a[end:]==b[ret:]
 assert old.RI==new.RI and old.RJ==new.RJ and old.KQ==new.KQ
 addr0,addr1,addr2=t['magnitude_lsb'];norm0=t['norm_before'][0]
 assert len({addr0,addr1,addr2,norm0})==4
 assert t['norm_middle']==(addr0,)+t['norm_before'][1:]
 protected=set(sum(old.RI,[])+sum(old.RJ,[]))|set(range(73,76))
 assert not any(q in protected for op in a[s:end] for q in op[1:4])
 assert not any(q in protected-{addr0} for op in b[lo:hi] for q in op[1:4])
 pins=set(old.KQ)|set(t['norm_before']);initial_map={q:q for q in pins};initial_map[norm0]=addr0
 mapping=initial_map.copy();births=retirements=0
 for i,(x,y) in enumerate(zip(a[s:end],b[lo:hi])):
  assert x[0]==y[0] and x[4:]==y[4:]
  for q,r in zip(x[1:4],y[1:4]):
   if q==NO:assert r==NO;continue
   if q not in mapping:
    assert r not in mapping.values();mapping[q]=r;births+=1
   assert mapping[q]==r,(i,q,r)
  if x[0] in (8,9):
   q=x[3];assert q not in pins;del mapping[q];retirements+=1
 assert mapping==initial_map
 # Only insert an observational attribute; emitted records must be unchanged.
 src=z.baseline.read_text();mark='    _MSQ = b.checkpoint()';assert src.count(mark)==1
 src=src.replace(mark,mark+'\n    b._peer_square_start = len(b.ops)')
 m=types.ModuleType('parity_peer_observe');m.__file__=str(z.baseline.resolve());sys.modules[m.__name__]=m
 with contextlib.redirect_stdout(io.StringIO()):exec(compile(src,m.__file__,'exec'),m.__dict__)
 assert list(m.b.ops)==a
 support={norm0};cone=[]
 for j in range(s-1,m.b._peer_square_start-1,-1):
  k,qa,qb,qt,*_=a[j]
  if k in (0,3,6,8,9) and qt in support:
   assert k==3;support.symmetric_difference_update({qb});cone.append(j)
  elif k==5 and ((qb in support)!=(qt in support)):
   support.symmetric_difference_update({qb,qt});cone.append(j)
 assert support=={norm0,addr0,addr1,addr2} and len(cone)==7
 bridge=b[s:lo]+b[hi:ret];assert len(bridge)==7
 def cases(ops):
  for x,y,zv in itertools.product(range(2),repeat=3):
   initial={addr0:x,addr1:y,addr2:zv,norm0:x^y^zv}
   got=scalar(ops,initial);assert got==initial
   borrowed=scalar(b[s:lo],initial)
   assert borrowed[addr0]==x^y^zv and borrowed[norm0]==0
 cases(bridge);mutants=0
 for i,op in enumerate(bridge):
  if op[0]!=3:continue
  try:cases(bridge[:i]+bridge[i+1:])
  except AssertionError:mutants+=1
  else:raise AssertionError('omitted CX accepted')
 assert mutants==6 and before==[sha(z.baseline),sha(z.candidate)]
 report={'status':'PASS','baseline_sha256':before[0],'candidate_sha256':before[1],
 'peer_sha256':sha(Path(__file__)),'upstream_commit':UP,
 'middle_records':end-s,'zero_target_rebindings':births,'zero_target_retirements':retirements,
 'prefix_and_suffix_byte_identical':True,'all_classical_record_fields_identical':True,
 'square_parity_projection_CX':len(cone),'square_begin':m.b._peer_square_start,
 'transfer_return_cases':8,'omitted_CX_mutants_rejected':mutants,
 'expanded_u64le_sha256':hashlib.sha256(b''.join(struct.pack('<9Q',*op)for op in b)).hexdigest(),
 'scope':'Conditional replacement of the published baseline interface: clean norm slot at squarer entry; exact magnitude parity supplied; middle has the baseline norm-restoration contract. Arbitrary middle record phase/outcome dependence is preserved under rolling wire renaming. This is not a new all-coordinate/all-accumulator theorem for the baseline. Fresh task-level verification is separately bound.',
 'independence':'Reuses upstream source emitter, not Simulator or the author allocation-log canonicalizer.'}
 out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
