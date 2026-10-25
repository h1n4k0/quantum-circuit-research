#!/usr/bin/env python3
"""Offline full replay of the finite HHL single-shear phase candidate."""
import argparse,hashlib,importlib.util,json,lzma,os,shutil,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
PIN='64b5a13aa249f1360846657392e6c66817b26d0f'
SOURCE='fc37886611a9245bab10d454ac4a07d538a534c28b3bdcbceeefda9211c3b1e7'
STREAM='709a93012bbc4f43ae4ea44457f72219fafecdab9f4fe2ab626e4ca8f359f05d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory():return {p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*') if p.is_file()}
def check_manifest():
 actual=inventory();del actual['MANIFEST.json']
 assert actual==json.loads((ROOT/'MANIFEST.json').read_text())['sha256']
 assert not any(p.is_symlink() for p in ROOT.rglob('*'))
 return inventory()
def check_upstream(up):
 assert subprocess.check_output(['git','-C',str(up),'rev-parse','HEAD'],text=True).strip()==PIN
 assert not subprocess.check_output(['git','-C',str(up),'status','--porcelain','--untracked-files=no'],text=True).strip()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repository',type=Path,required=True);ap.add_argument('--upstream',type=Path,required=True);ap.add_argument('--numeric-certificate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 repo=a.repository.resolve();up=a.upstream.resolve();numeric=a.numeric_certificate.resolve();out=a.output.resolve()
 assert not out.exists()
 for p in (ROOT,repo,up,numeric):assert out!=p and p not in out.parents,'output inside frozen input'
 for p in (out,*out.parents):assert not any((p/n).exists() for n in ('MANIFEST.json','PUBLICATION_MANIFEST.json')),'output inside manifested input'
 before=check_manifest();check_upstream(up);start=time.monotonic()
 source=ROOT/'task/circuits/shear/circuit.py';assert sha(source)==SOURCE
 base=repo/'checkpoints/hhl-octave-tensor/candidate'
 for name in ('contract.json','grader.py','reference.py'):assert (ROOT/'task'/name).read_bytes()==(up/'tasks/hhl-angle'/name).read_bytes()
 out.mkdir(parents=True);task=out/'task';task.mkdir()
 for name in ('contract.json','grader.py','reference.py'):shutil.copyfile(ROOT/'task'/name,task/name)
 candidate=task/'circuits/shear';shutil.copytree(source.parent,candidate)
 baseline=task/'circuits/octave-tensor';shutil.copytree(base,baseline)
 env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(up)
 env.pop('UNCOMPUTE_OPS_PATH',None)
 def run(name,args):
  with (out/(name+'.log')).open('w') as f:subprocess.run([sys.executable,'-B',*map(str,args)],check=True,env=env,stdout=f,stderr=subprocess.STDOUT)
 run('construction',[ROOT/'construction/build_candidate.py','--baseline',base,'--screens',ROOT/'construction/upper-octaves.json',ROOT/'construction/lower-octaves.json','--output',out/'regenerated'])
 for n in ('circuit.py','constants.json','phase_plan.json'):assert (out/'regenerated'/n).read_bytes()==(candidate/n).read_bytes()
 # Recompute the complete polarity/partition search for the selected shear.
 spec=importlib.util.spec_from_file_location('finite_shear_screen',ROOT/'construction/screen.py');screen=importlib.util.module_from_spec(spec);spec.loader.exec_module(screen)
 data=json.loads((candidate/'constants.json').read_text());leaves=data['leaves'];raw=[]
 for x in range(1<<18,1<<19,1<<11):
  matches=[j for j,(lo,bb) in enumerate(zip(leaves['lo'],leaves['bb'])) if lo<=x<lo+(1<<bb)]
  assert len(matches)==1;j=matches[0]
  raw.append(leaves['g2'][j]|(leaves['sh'][j]<<5)|((leaves['g1'][j]+4096)<<8)|((leaves['g0'][j]>>6)<<24))
 selected=screen.run((18,11,raw,[1,5]));assert json.loads(json.dumps(selected))==json.loads((candidate/'phase_plan.json').read_text())['plans'][2]
 metrics={}
 for name,circuit in [('candidate',candidate/'circuit.py'),('baseline',baseline/'circuit.py'),('released',up/'tasks/hhl-angle/circuits/discovered/circuit.py')]:
  run(name,[up/'tools/eval.py','hhl-angle','--circuit',circuit,'--out',out/name,'--capture',out/(name+'.ops'),'--jobs','1','--json'])
  report=json.loads((out/name/'report.json').read_text());assert report['verdict']=='OK';metrics[name]=report['metrics']
 assert (out/'candidate.ops').read_bytes()==lzma.decompress((candidate/'circuit.ops.xz').read_bytes())
 assert sha(out/'candidate.ops')==STREAM
 run('stored',[up/'tools/eval.py','hhl-angle','--ops',candidate/'circuit.ops.xz','--out',out/'stored','--jobs','1','--json'])
 stored=json.loads((out/'stored/report.json').read_text());assert stored['verdict']=='OK' and stored['h_ops']==STREAM
 for name,script in [('strict','audit_hhl_candidate.py'),('suffix','verify_octave_suffix.py')]:
  run(name,[ROOT/'verification'/script,candidate/'circuit.py','--upstream',up,'--output',out/(name+'.json')])
  assert json.loads((out/(name+'.json')).read_text())['status']=='PASS'
 run('numeric',[numeric/'reproduce.py','--candidate',base,'--upstream',up,'--output',out/'numeric'])
 run('numeric_transfer',[ROOT/'verification/transfer_numeric_certificate.py','--baseline',baseline/'circuit.py','--candidate',candidate/'circuit.py','--numeric-report',out/'numeric/report.json','--upstream',up,'--output',out/'numeric_transfer.json'])
 expected={'candidate':(1205,115,13601),'baseline':(1206,115,13601),'released':(1348,115,56419)}
 for name,want in expected.items():assert tuple(metrics[name][k] for k in ('toffoli','qubits','clifford'))==want
 assert check_manifest()==before;check_upstream(up)
 result={'status':'PASS','upstream_commit':PIN,'source_sha256':SOURCE,'stream_sha256':STREAM,'metrics':metrics,
  'construction_byte_identical':True,'selected_shear_plan_regenerated':True,'source_and_stored_streams_equal':True,'frozen_package_unchanged':True,
  'evidence_sha256':{n:sha(out/n) for n in ('candidate/report.json','baseline/report.json','released/report.json','stored/report.json','strict.json','suffix.json','numeric/report.json','numeric_transfer.json')},
  'scope':'Same arithmetic prefix and exact numerical-model bound; complete suffix component proof under incoming-phase contract; whole-circuit gate verification still limited to 71424 witness cases and sampled official shots. Logical resources only; no global optimum or hardware claim.',
  'seconds':time.monotonic()-start}
 (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
