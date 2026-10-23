#!/usr/bin/env python3
"""Fail-closed binding of a fresh source emission to two existing verification reports.

No new exhaustive theorem: the selected original strict audit and official evaluator
remain the computational trust base. This binder independently reloads the source,
compares the complete stream bytes, and checks source/report identity and metrics.
"""
import argparse,contextlib,hashlib,io,json,subprocess,sys,time
from pathlib import Path
PIN='64b5a13aa249f1360846657392e6c66817b26d0f'
AUDITS={'hhl':'123dd9dcb0454f41ffad42a6128fdedc6bc573b0f5c62fbc33a250a0f012336c'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['source','upstream','official','audit','audit-script','raw','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--task',choices=['hhl','coulomb'],required=True);a=p.parse_args()
 out=a.output.resolve(); assert not out.exists(),'fresh output required'
 inputs=[a.source,a.official,a.audit,a.audit_script,a.raw]
 for f in inputs:assert f.is_file(),f
 assert out not in [f.resolve() for f in inputs]
 assert not(a.upstream.resolve()==out or a.upstream.resolve() in out.parents)
 for base in [Path(__file__).resolve(),a.source.resolve()]:
  for root in base.parents:
   if (root/'MANIFEST.json').exists(): assert not(out==root or root in out.parents),'frozen container'
 assert subprocess.check_output(['git','-C',str(a.upstream),'rev-parse','HEAD'],text=True).strip()==PIN
 assert not subprocess.check_output(['git','-C',str(a.upstream),'diff','--name-only','HEAD','--'],text=True).strip()
 before={str(i):sha(i) for i in inputs};t=time.monotonic()
 if a.task=='hhl':assert sha(a.audit_script)==AUDITS['hhl']
 sys.path.insert(0,str(a.upstream.resolve()));from uncompute.testing import load_module
 with contextlib.redirect_stdout(io.StringIO()):m=load_module(a.source.resolve(),'bound_candidate',register=True)
 with contextlib.redirect_stdout(io.StringIO()):b=m.build()[0] if a.task=='hhl' else m.b
 captured=io.BytesIO();b.emit(meta=False,dest=captured)
 raw=captured.getvalue();assert raw==a.raw.read_bytes(),'source emission differs from certified stream'
 official=json.loads(a.official.read_text());audit=json.loads(a.audit.read_text())
 assert official['verdict']=='OK' and all(v==0 for v in official['counters'].values())
 assert official['h_ops']==hashlib.sha256(raw).hexdigest()
 assert audit['status']=='PASS' and audit['candidate_sha256']==sha(a.source)
 assert audit['metrics']['toffoli']==official['metrics']['toffoli']
 assert audit['metrics']['peak_logical_qubits']==official['metrics']['qubits']
 n=71424 if a.task=='hhl' else 837822
 assert audit['scope']['gate_level_cases']==n
 ops=list(b.ops);assert sum(op[0]==6 for op in ops)==official['metrics']['toffoli']
 assert before=={str(i):sha(i) for i in inputs},'inputs moved during verification'
 result={'status':'PASS','upstream_commit':PIN,'task':a.task,
 'source_sha256':sha(a.source),'raw_sha256':hashlib.sha256(raw).hexdigest(),'raw_bytes':len(raw),
 'source_emission_byte_identical':True,'actual_flat_records':len(ops),
 'metrics':official['metrics'],'TQ':official['metrics']['toffoli']*official['metrics']['qubits'],
 'scope':audit['scope'],'strict_report_sha256':sha(a.audit),'official_report_sha256':sha(a.official),
 'audit_script_sha256':sha(a.audit_script),'binder_sha256':sha(Path(__file__)),
 'limitations':'Fresh independent invocation, not an independent simulator implementation. Official cases are sampled. Strict all-outcome checking applies to the stated basis-input tests, not every coordinate/accumulator. Logical Toffoli/Q proxies do not claim hardware speed.',
 'wall_seconds':time.monotonic()-t}
 out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
