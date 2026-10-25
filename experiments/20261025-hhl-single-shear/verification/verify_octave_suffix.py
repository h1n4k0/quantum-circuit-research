#!/usr/bin/env python3
"""Independent bitset/affine-draw certificate for the actual final phase suffix.

Imports the upstream Builder to capture emission, but never executes Simulator.
The component's incoming phase is the coefficient measurement debt; this is an
explicit component precondition, not a new proof of the arithmetic prefix.
"""
import argparse,bisect,hashlib,json,struct,sys,types
from pathlib import Path
N=(1<<64)-1
REQ={0:{3},1:{3},2:set(),3:{2,3},4:{2,3},5:{2,3},6:{1,2,3},7:{1,2,3},8:{3},9:{3,4},10:{4,5}}
QFIELDS={0:(3,),1:(3,),2:(),3:(2,3),4:(2,3),5:(2,3),6:(1,2,3),7:(1,2,3),8:(3,),9:(3,),10:()}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def grammar(ops):
 for o in ops:
  k=o[0];assert k in REQ and len(o)==9
  used=set(REQ[k]);used|={5} if k in (1,2,4) and o[5]!=N else set()
  assert all((0<=o[i]<2**32) if i in used else o[i]==N for i in range(1,9)),o
  qs=[o[i] for i in QFIELDS[k]];assert len(set(qs))==len(qs)
  if k==10:assert o[4]!=o[5]
def packed_words(constants):
 c=json.loads(constants.read_text());g=c['cfg'];l=c['leaves'];out=[]
 assert g['G2W']==5 and g['G1W']==16 and g['C0DROP']==6
 cursor=65536
 for lo,bb in zip(l['lo'],l['bb']):assert lo==cursor;cursor=lo+(1<<bb)
 assert cursor==1<<21
 for x in range(65536,1<<21,256):
  j=bisect.bisect_right(l['lo'],x)-1;assert x+255<l['lo'][j]+(1<<l['bb'][j])
  fields=((l['g2'][j],5),(l['sh'][j],3),(l['g1'][j]+4096,16),(l['g0'][j]//64,26))
  word=0;shift=0
  for v,w in fields:assert 0<=v<1<<w;word|=v<<shift;shift+=w
  out.append(word)
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--upstream',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 source=a.source.resolve();const=source.with_name('constants.json');plan=source.with_name('phase_plan.json');before={p.name:digest(p) for p in (source,const,plan)}
 sys.path[:0]=[str(a.upstream.resolve()),str(source.parent)];captured={}
 def hook(b,loc):
  captured.update(cut=len(b.ops),x=list(loc['XQ']),k=list(loc['KQ']),outcomes=[m.id for name in ('mb_g2','mb_sh','mb_g1','mb_c0') for m in loc[name]])
 def build(capture):
  mod=types.ModuleType('suffix_capture' if capture else 'plain_source');mod.__file__=str(source);mod.__dict__['_capture_hook']=hook
  s=source.read_text();assert s.count('    # ---- 9.')==1
  if capture:s=s.replace('    # ---- 9.','    _capture_hook(b, locals())\n    # ---- 9.',1)
  exec(compile(s,str(source),'exec'),mod.__dict__);return mod.build()[0]
 plain=build(False);instrumented=build(True);allops=list(plain.ops);assert allops==list(instrumented.ops);grammar(allops)
 cut=captured['cut'];prefix=allops[:cut];suffix=allops[cut:];x=captured['x'];protected=set(x[:8]+captured['k']);assert len(captured['outcomes'])==50 and len(set(captured['outcomes']))==50
 touched={o[i] for o in suffix for i in QFIELDS[o[0]]};assert not touched&protected
 workspace=touched-set(x);last={}
 for i,o in enumerate(prefix):
  for j in QFIELDS[o[0]]:last[o[j]]=(i,o)
 for w in workspace:
  assert w not in set(x+captured['k'])
  if w in last:assert last[w][1][0] in (8,9) and last[w][1][3]==w,(w,last[w])
 prefix_out={o[4] for o in prefix if o[0] in (9,10)}
 words=packed_words(const);batch=len(words);assert batch==7936;mask=(1<<batch)-1
 cols=[sum(((v>>j)&1)<<i for i,v in enumerate(words)) for j in range(50)]
 initial={q:sum((((256+i)>>(j-8))&1)<<i for i in range(batch)) for j,q in enumerate(x) if j>=8}
 def replay(ops):
  q=dict(initial);ledger=list(cols);out={oid:1<<i for i,oid in enumerate(captured['outcomes'])};constant=0
  def phase(f,oid):
   nonlocal constant
   if oid==N:constant^=f;return
   assert oid in out;v=out[oid]
   while v:
    bit=v&-v;ledger[bit.bit_length()-1]^=f;v^=bit
  for o in ops:
   k,qa,qb,qt,ot,oc,_,_,_=o
   if k==0:q[qt]=q.get(qt,0)^mask
   elif k==3:q[qt]=q.get(qt,0)^q.get(qb,0)
   elif k==6:q[qt]=q.get(qt,0)^(q.get(qa,0)&q.get(qb,0))
   elif k==5:q[qb],q[qt]=q.get(qt,0),q.get(qb,0)
   elif k==1:phase(q.get(qt,0),oc)
   elif k==2:phase(mask,oc)
   elif k==4:phase(q.get(qb,0)&q.get(qt,0),oc)
   elif k==7:phase(q.get(qa,0)&q.get(qb,0)&q.get(qt,0),N)
   elif k==8:assert not q.get(qt,0)
   elif k==9:out[ot]=1<<len(ledger);ledger.append(q.get(qt,0));q[qt]=0
   elif k==10:
    assert oc in out
    if ot not in out:assert ot not in prefix_out;out[ot]=0
    out[ot]^=out[oc]
  assert not constant and not any(ledger)
  assert all(q.get(w,0)==initial.get(w,0) for w in touched|set(initial))
  return len(ledger)-50
 draws=replay(suffix);mutation=False
 for i,o in enumerate(suffix):
  if o[0]!=4:continue
  try:replay(suffix[:i]+suffix[i+1:])
  except AssertionError:mutation=True;break
 assert mutation
 assert before=={p.name:digest(p) for p in (source,const,plan)}
 result={'status':'PASS','source_files':before,'verifier_sha256':digest(Path(__file__)),'actual_expanded_ops_sha256':hashlib.sha256(b''.join(struct.pack('<9Q',*o) for o in allops)).hexdigest(),'capture_equals_uninstrumented':True,'canonical_ops_checked':len(allops),'suffix_start':cut,'suffix_ops':len(suffix),'valid_selector_classes':batch,'initial_independent_coefficient_outcomes':50,'additional_fresh_draws':draws,'all_draw_assignments':True,'workspace_zero_entry':'each non-interface wire never touched or last touched by unconditional R/HMR','lower8_X_and_all_K':'structurally untouched by suffix','mutation_missing_CZ_rejected':True,'scope':'Conditional component certificate: incoming phase is exactly the 50 coefficient measurement debts and workspace is clean. No independent proof of arithmetic-prefix correctness or all accumulators is claimed. Invalid selector classes 0..255 are excluded.'}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
