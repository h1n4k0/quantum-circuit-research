#!/usr/bin/env python3
"""Reproduce the recovered public HHL checkpoint; no new optimization claim.

Requires the upstream checkout and the public repository's initial-001 directory.
Creates a fresh output directory; never edits either input. Python, NumPy,
Click and the optional locally compiled upstream kernel are the only dependencies.
"""
import argparse, hashlib, json, lzma, platform, shutil, subprocess, sys, time
from pathlib import Path

UPSTREAM = '64b5a13aa249f1360846657392e6c66817b26d0f'
SOURCE = '12d60c4d8963f8eafc5f90abb4d446391100d4d84b9560cba0f6b68b7fa0a6c5'
CONSTANTS = '09e9d869cf54ec76361641aab0a83fa1122b2051ad383def3da16dae12e95370'
AUDIT = '123dd9dcb0454f41ffad42a6128fdedc6bc573b0f5c62fbc33a250a0f012336c'
OPS = 'b6041c74cdbee72641967a11fb54318d4776204c84785942133f6e6698c64eea'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--upstream',type=Path,required=True)
 p.add_argument('--snapshot',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();u=a.upstream.resolve();s=a.snapshot.resolve();o=a.output.resolve()
 assert not o.exists(), 'fresh output required'
 assert not (o == Path(__file__).resolve().parent or Path(__file__).resolve().parent in o.parents), 'output must be outside package'
 for parent in Path(__file__).resolve().parents:
  if (parent / 'MANIFEST.json').is_file():
   assert not (o == parent or parent in o.parents), 'output must be outside frozen ancestor'
 assert not subprocess.check_output(['git','-C',str(u),'diff','--name-only','HEAD','--'],text=True).strip(), 'upstream tracked files modified'
 assert not (o==u or u in o.parents or o==s or s in o.parents), 'output must be outside inputs'
 assert subprocess.check_output(['git','-C',str(u),'rev-parse','HEAD'],text=True).strip()==UPSTREAM
 c=s/'candidates/hhl/anf_v1'; audit=s/'verification/audit_hhl_candidate.py'
 assert sha(audit)==AUDIT, 'published audit source mismatch'
 assert sha(c/'circuit.py')==SOURCE and sha(c/'constants.json')==CONSTANTS
 frozen=lzma.decompress((c/'circuit.ops.xz').read_bytes());assert hashlib.sha256(frozen).hexdigest()==OPS
 pins={str(x.relative_to(s)):sha(x) for x in [c/'circuit.py',c/'constants.json',c/'circuit.ops.xz',audit]}
 t=time.monotonic();o.mkdir(parents=True)
 task=o/'tasks/hhl-angle';shutil.copytree(u/'tasks/hhl-angle',task)
 copied=task/'circuits/research-initial-001';shutil.copytree(c,copied)
 def run(label,args):
  with (o/(label+'.log')).open('w') as log:
   subprocess.run([sys.executable,*map(str,args)],stdout=log,stderr=subprocess.STDOUT,check=True)
 ev=u/'tools/eval.py'
 run('released',[ev,'hhl-angle','--out',o/'released','--capture',o/'released.ops','--jobs','1','--json'])
 run('source',[ev,'hhl-angle','--circuit',copied/'circuit.py','--out',o/'source','--capture',o/'source.ops','--jobs','1','--json'])
 run('stored',[ev,'hhl-angle','--ops',c/'circuit.ops.xz','--out',o/'stored','--jobs','1','--json'])
 run('strict',[audit,copied/'circuit.py','--upstream',u,'--output',o/'strict.json'])
 assert (o/'source.ops').read_bytes()==frozen
 rr={n:json.loads((o/n/'report.json').read_text()) for n in ['released','source','stored']}
 assert all(x['verdict']=='OK' for x in rr.values())
 assert rr['released']['metrics']['toffoli']==1348 and rr['released']['metrics']['qubits']==115
 for n in ['source','stored']:
  assert rr[n]['h_ops']==OPS and rr[n]['metrics']['toffoli']==1273 and rr[n]['metrics']['qubits']==115
 strict=json.loads((o/'strict.json').read_text());assert strict['status']=='PASS'
 assert strict['scope']['gate_level_cases']==71424 and strict['scope']['full_arithmetic_domain_values']==2031616
 assert pins=={str(x.relative_to(s)):sha(x) for x in [c/'circuit.py',c/'constants.json',c/'circuit.ops.xz',audit]}
 summary={'status':'PASS','upstream_commit':UPSTREAM,'python':platform.python_version(),
  'input_sha256':pins,'source_stream_sha256':OPS,'source_and_stored_bytes_identical':True,
  'metrics':{n:x['metrics'] for n,x in rr.items()},'strict_scope':strict['scope'],
  'max_error_integer_units':strict['max_error_integer_units'],'max_error_radians':strict['max_error_radians'],
  'evidence_sha256':{str(x.relative_to(o)):sha(x) for x in [o/'released/report.json',o/'source/report.json',o/'stored/report.json',o/'strict.json',o/'source.ops',o/'released.ops']},
  'scope':'Fresh reproduction of recovered initial-001, not restoration of later lost candidates. Official tests are sampled; full arithmetic-model and 71424 gate checks do not prove all accumulators. Simulator and numerical model are upstream implementations.',
  'wall_seconds':time.monotonic()-t}
 (o/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
