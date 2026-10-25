#!/usr/bin/env python3
"""Fail-before-write tests for new public entry points."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repository',type=Path,required=True);ap.add_argument('--upstream',type=Path,required=True);ap.add_argument('--numeric-certificate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 repo=a.repository.resolve();up=a.upstream.resolve();numeric=a.numeric_certificate.resolve();out=a.output.resolve()
 assert not out.exists()
 for p in (ROOT,repo,up,numeric):assert out!=p and p not in out.parents
 for p in (out,*out.parents):assert not any((p/n).exists() for n in ('MANIFEST.json','PUBLICATION_MANIFEST.json'))
 out.mkdir(parents=True)
 base=repo/'checkpoints/hhl-octave-tensor/candidate';candidate=ROOT/'task/circuits/shear/circuit.py'
 entries={
  'reproduce':[ROOT/'reproduce.py','--repository',repo,'--upstream',up,'--numeric-certificate',numeric],
  'constructor':[ROOT/'construction/build_candidate.py','--baseline',base,'--screens',ROOT/'construction/upper-octaves.json'],
  'screen':[ROOT/'construction/screen.py','--constants',base/'constants.json'],
  'transfer':[ROOT/'verification/transfer_numeric_certificate.py','--baseline',base/'circuit.py','--candidate',candidate,'--numeric-report',numeric/'results/numeric_standalone.json','--upstream',up],
  'guard_runner':[Path(__file__).resolve(),'--repository',repo,'--upstream',up,'--numeric-certificate',numeric],
 }
 targets={'existing':out,'package':ROOT/'must-not-create','candidate':base/'must-not-create'}
 for marker in ('MANIFEST.json','PUBLICATION_MANIFEST.json'):
  container=out/marker;container.mkdir();(container/marker).write_text('{}\n');targets[marker]=container/'must-not-create'
 results=[]
 for name,command in entries.items():
  for kind,target in targets.items():
   p=subprocess.run([sys.executable,'-B',*map(str,command),'--output',str(target)],capture_output=True,text=True)
   assert p.returncode!=0,(name,kind)
   if kind!='existing':assert not target.exists(),(name,kind)
   results.append({'entry':name,'target':kind,'rejected_before_write':True})
 report={'status':'PASS','cases':len(results),'tests':results,
         'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
