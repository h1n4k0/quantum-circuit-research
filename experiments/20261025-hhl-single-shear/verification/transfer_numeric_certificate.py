#!/usr/bin/env python3
"""Bind unchanged emitted arithmetic prefix to the rigorous HHL numeric result.

This is a transfer of a numerical-model certificate, not an all-accumulator
whole-circuit gate theorem. The changed suffix has its own component proof.
"""
import argparse,ast,hashlib,json,struct,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
BASE='d854ac76c46919b83568c307767049b241c19655b84330ba1cfd2b713df09f37'
CANDIDATE='fc37886611a9245bab10d454ac4a07d538a534c28b3bdcbceeefda9211c3b1e7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(path):
 tree=ast.parse(path.read_text().split('    # ---- 9.')[0])
 tree.body=[n for n in tree.body if not(isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))]
 return ast.dump(tree,include_attributes=False)
def capture(path,name):
 source=path.read_text();assert source.count('    # ---- 9.')==1;cut={}
 def hook(b,loc):cut.update(index=len(b.ops),x=loc['XQ'],k=loc['KQ'],outcomes=[m.id for key in ('mb_g2','mb_sh','mb_g1','mb_c0') for m in loc[key]])
 def build(instrument):
  mod=types.ModuleType(name+str(instrument));mod.__file__=str(path);mod.__dict__['_hook']=hook
  code=source.replace('    # ---- 9.','    _hook(b,locals())\n    # ---- 9.',1) if instrument else source
  exec(compile(code,str(path),'exec'),mod.__dict__);return mod.build()[0]
 plain=build(False);traced=build(True);assert list(plain.ops)==list(traced.ops)
 return list(plain.ops)[:cut['index']],cut
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--numeric-report',type=Path,required=True);ap.add_argument('--upstream',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 out=a.output.resolve();assert not out.exists()
 for p in (out,*out.parents):assert not any((p/n).exists() for n in ('MANIFEST.json','PUBLICATION_MANIFEST.json'))
 for p in (a.baseline.resolve().parent,a.candidate.resolve().parent,Path(__file__).resolve().parents[1]):assert p!=out and p not in out.parents
 assert sha(a.baseline)==BASE and sha(a.candidate)==CANDIDATE
 assert sha(a.baseline.with_name('constants.json'))==sha(a.candidate.with_name('constants.json'))
 assert normalized(a.baseline)==normalized(a.candidate)
 sys.path.insert(0,str(a.upstream.resolve()))
 base,bc=capture(a.baseline.resolve(),'base');candidate,cc=capture(a.candidate.resolve(),'candidate')
 assert base==candidate and bc==cc
 report=json.loads(a.numeric_report.read_text());assert report['status']=='PASS' and report['source_sha256']==BASE
 assert report['constants_sha256']==sha(a.candidate.with_name('constants.json'))
 numeric=report['integer_certificate'];assert numeric['domain_values']==2031616
 assert numeric['max_real_error_numerator_upper']==114661270226 and numeric['real_error_denominator_output_units']==1<<28
 result={'status':'PASS','candidate_sha256':CANDIDATE,'baseline_sha256':BASE,
  'constants_sha256':report['constants_sha256'],'numeric_report_sha256':sha(a.numeric_report),
  'verifier_sha256':sha(Path(__file__)),'normalized_executable_prefix_equal':True,
  'actual_uninstrumented_emitted_prefix_equal':True,'prefix_operations':len(base),
  'prefix_u64le_sha256':hashlib.sha256(b''.join(struct.pack('<9Q',*o) for o in base)).hexdigest(),
  'coefficient_outcomes_and_persistent_registers_equal':True,'integer_certificate':numeric,
  'scope':'Exact unchanged-prefix transfer of the full-domain numerical-model enclosure. The separate suffix checker covers all 7936 valid selector classes and all measurement outcomes under its incoming-phase contract. No new whole-circuit all-input/all-accumulator theorem.'}
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
