#!/usr/bin/env python3
"""Reproduce the frozen HHL per-octave phase candidate and fair baselines."""
import argparse,hashlib,json,lzma,shutil,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
PINS={'circuit.py':'d854ac76c46919b83568c307767049b241c19655b84330ba1cfd2b713df09f37','constants.json':'09e9d869cf54ec76361641aab0a83fa1122b2051ad383def3da16dae12e95370','phase_plan.json':'60b5533f8a53a919ea9b1af9abc43a85261f63a65b6a663a5e148712574efc94'}
OPS='af7fde268a5415124463b82a982af34faeb8cde9db744fdaa7bf05b630698559'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--upstream',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();o=a.output.resolve();u=a.upstream.resolve();s=a.snapshot.resolve()
 assert not o.exists(),'fresh output required'
 for forbidden in [ROOT,u,s]+[p for p in ROOT.parents if (p/'MANIFEST.json').is_file()]:assert o!=forbidden and forbidden not in o.parents,'output inside protected input/container'
 assert subprocess.check_output(['git','-C',str(u),'rev-parse','HEAD'],text=True).strip()=='64b5a13aa249f1360846657392e6c66817b26d0f'
 assert not subprocess.check_output(['git','-C',str(u),'diff','--name-only','HEAD','--'],text=True).strip()
 assert {n:sha(ROOT/'candidate'/n) for n in PINS}==PINS
 assert sha(ROOT/'verification/audit_hhl_candidate.py')=='123dd9dcb0454f41ffad42a6128fdedc6bc573b0f5c62fbc33a250a0f012336c'
 assert sha(ROOT/'verification/verify_octave_suffix.py')=='79ec160565b992a8a4e49754375b7712f6746d3fac3c4612794d23fb7ef4b69b'
 if (ROOT/'MANIFEST.json').exists():
  m=json.loads((ROOT/'MANIFEST.json').read_text());assert all(sha(ROOT/f)==h for f,h in m['files'].items())
 t=time.monotonic();o.mkdir(parents=True)
 def run(name,args):
  with (o/(name+'.log')).open('w') as log:subprocess.run([sys.executable,'-B',*map(str,args)],stdout=log,stderr=subprocess.STDOUT,check=True)
 run('baseline',[ROOT/'verification/reproduce_baseline.py','--upstream',u,'--snapshot',s,'--output',o/'baseline'])
 task=o/'tasks/hhl-angle';shutil.copytree(u/'tasks/hhl-angle',task);cand=task/'circuits/octave-tensor';shutil.copytree(ROOT/'candidate',cand)
 ev=u/'tools/eval.py'
 run('candidate',[ev,'hhl-angle','--circuit',cand/'circuit.py','--out',o/'official','--capture',o/'candidate.ops','--jobs','1','--json'])
 frozen=lzma.decompress((cand/'circuit.ops.xz').read_bytes());assert (o/'candidate.ops').read_bytes()==frozen and hashlib.sha256(frozen).hexdigest()==OPS
 run('stored',[ev,'hhl-angle','--ops',cand/'circuit.ops.xz','--out',o/'stored','--jobs','1','--json'])
 run('strict',[ROOT/'verification/audit_hhl_candidate.py',cand/'circuit.py','--upstream',u,'--output',o/'strict.json'])
 run('suffix',[ROOT/'verification/verify_octave_suffix.py',cand/'circuit.py','--upstream',u,'--output',o/'suffix.json'])
 sys.path.insert(0,str(ROOT/'discovery'));from design_octave_tensor_phase import plan
 assert json.loads(json.dumps(plan(cand/'constants.json')))==json.loads((cand/'phase_plan.json').read_text())['plans']
 official=json.loads((o/'official/report.json').read_text());stored=json.loads((o/'stored/report.json').read_text());strict=json.loads((o/'strict.json').read_text());suffix=json.loads((o/'suffix.json').read_text())
 assert all(r['verdict']=='OK' and r['h_ops']==OPS and r['metrics']['toffoli']==1206 and r['metrics']['qubits']==115 for r in (official,stored))
 assert strict['status']==suffix['status']=='PASS'
 assert {n:sha(ROOT/'candidate'/n) for n in PINS}==PINS
 summary={'status':'PASS','candidate_sha256':PINS,'captured_stored_bytes_equal':True,'stream_sha256':OPS,'metrics':official['metrics'],'strict_scope':strict['scope'],'suffix_scope':suffix['scope'],'selected_plans_regenerated_exactly':True,'seconds':time.monotonic()-t,'evidence_sha256':{n:sha(o/n) for n in ['baseline/summary.json','official/report.json','stored/report.json','strict.json','suffix.json','candidate.ops']}}
 (o/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
