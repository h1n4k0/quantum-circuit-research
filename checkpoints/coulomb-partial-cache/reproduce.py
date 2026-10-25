#!/usr/bin/env python3
"""Offline, immutable-input verification against the pinned upstream checkout."""
import argparse,hashlib,json,lzma,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PIN='64b5a13aa249f1360846657392e6c66817b26d0f'
SOURCE='1379ef3398d3ac735bee2d4c4c4c045b77cce0500db506d91163a6fbfcc11cb7'
RAW='e4dbbbc9cc2db8f76afb4c8713efd04ec9ee351b154e77a969ee1034d03f65a9'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--upstream',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);a=ap.parse_args()
    up=a.upstream.resolve();out=a.output.resolve()
    # Do not write inside this publication container or any manifested ancestor.
    assert out!=ROOT.parent and ROOT.parent not in out.parents,'output inside publication container'
    assert out!=up and up not in out.parents,'output inside upstream'
    for par in (out,*out.parents):
        assert not (par/'MANIFEST.json').exists(),'output within a manifested artifact'
    assert not out.exists(),'output must be new'
    assert subprocess.check_output(['git','-C',str(up),'rev-parse','HEAD'],text=True).strip()==PIN
    assert subprocess.check_output(['git','-C',str(up),'status','--porcelain','--untracked-files=no'],text=True)==''
    assert sha(ROOT/'candidate/circuit.py')==SOURCE
    before={p.relative_to(ROOT).as_posix():sha(p)for p in ROOT.rglob('*')if p.is_file()}
    raw=lzma.decompress((ROOT/'candidate/circuit.ops.xz').read_bytes());assert hashlib.sha256(raw).hexdigest()==RAW
    out.mkdir(parents=True);t0=time.monotonic();task=out/'task';candidate=task/'circuits/partial_cache19_v1';candidate.mkdir(parents=True)
    for name in ('contract.json','grader.py','reference.py'):shutil.copyfile(up/'tasks/coulomb-potential'/name,task/name)
    for name in ('circuit.py','meta.json'):shutil.copyfile(ROOT/'candidate'/name,candidate/name)
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(up);env['UNCOMPUTE_OPS_PATH']=str(out/'emitted.ops')
    def run(name,args):
        with (out/(name+'.log')).open('w')as f:subprocess.run([sys.executable,*map(str,args)],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    run('emit',[candidate/'circuit.py']);assert sha(out/'emitted.ops')==RAW
    run('component',[ROOT/'verification/certify_partial_cache_lookup.py',candidate/'circuit.py','--upstream',up,'--output',out/'component.json'])
    run('domain_audit',[ROOT/'verification/audit_coulomb_candidate.py',candidate/'circuit.py','--upstream',up,'--output',out/'domain_audit.json'])
    run('official',[up/'tools/eval.py','coulomb-potential','--ops',out/'emitted.ops','--out',out/'official'])
    comp=json.loads((out/'component.json').read_text());audit=json.loads((out/'domain_audit.json').read_text());official=json.loads((out/'official/report.json').read_text())
    assert comp['status']==audit['status']=='PASS' and official['verdict']=='OK'
    assert audit['scope']['gate_level_cases']==837822
    assert comp['actual_lookup']=={'independent_hmr_draws':27,'toffoli':107,'symbolic_dirty_outputs':24,'addresses':128,'operations':2415}
    assert official['metrics']['toffoli']==1097 and official['metrics']['qubits']==142 and official['metrics']['clifford']==7285
    after={p.relative_to(ROOT).as_posix():sha(p)for p in ROOT.rglob('*')if p.is_file()};assert before==after,'artifact modified during replay'
    result={'status':'PASS','source_sha256':SOURCE,'raw_ops_sha256':RAW,'upstream_commit':PIN,'metrics':official['metrics'],'component':comp['actual_lookup'],'whole_circuit_scope':audit['scope'],'artifact_unchanged':True,'wall_seconds':time.monotonic()-t0}
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
