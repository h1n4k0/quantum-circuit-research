#!/usr/bin/env python3
"""Fresh official, integer-oracle, and actual-interface replay into a NEW directory."""
import argparse,hashlib,json,lzma,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PIN='64b5a13aa249f1360846657392e6c66817b26d0f'
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inside(p,r):return p==r or r in p.parents
def verify_manifest():
    m=json.loads((ROOT/'MANIFEST.json').read_text())['files']
    assert {str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()}==set(m)|{'MANIFEST.json'}
    for n,h in m.items():assert sh(ROOT/n)==h,n
    return sh(ROOT/'MANIFEST.json')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--upstream',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();out=a.output.resolve();up=a.upstream.resolve()
    # Reject before mkdir: whole containing checkpoint collection and every
    # manifested ancestor, not merely this single payload directory.
    if out.exists():raise SystemExit('Output exists; choose a fresh directory')
    protected=[ROOT.parent]+[p for p in ROOT.parents if any((p/f).exists() for f in ('MANIFEST.json','PUBLICATION_MANIFEST.json'))]
    if any(inside(out,p) for p in protected):raise SystemExit('Output is inside a protected checkpoint container')
    manifest_hash=verify_manifest()
    assert subprocess.check_output(['git','-C',str(up),'rev-parse','HEAD'],text=True).strip()==PIN
    assert not subprocess.check_output(['git','-C',str(up),'status','--porcelain','--untracked-files=no'],text=True).strip()
    out.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['UNCOMPUTE_KERNEL']='1';env['PYTHONPATH']=str(up)
    candidate=ROOT/'task/circuits/norm_parity_alias_v1/circuit.py'
    baseline=ROOT/'task/circuits/baseline/circuit.py'
    def run(name,cmd):
        with (out/(name+'.stdout.log')).open('w') as stdout,(out/(name+'.stderr.log')).open('w') as stderr:
            subprocess.run(cmd,check=True,env=env,stdout=stdout,stderr=stderr)
    run('kernel',['make','-C',str(up),'kernel'])
    run('official',[sys.executable,'-B',str(up/'tools/eval.py'),'coulomb-potential','--circuit',str(candidate),'--capture',str(out/'emitted.ops'),'--out',str(out/'official')])
    run('independent',[sys.executable,'-B',str(ROOT/'verification/audit_coulomb_candidate.py'),str(candidate),'--upstream',str(up),'--output',str(out/'independent.json')])
    run('interface',[sys.executable,'-B',str(ROOT/'verification/certify_norm_parity_alias_v2.py'),str(candidate),'--baseline',str(baseline),'--upstream',str(up),'--output',str(out/'interface.json')])
    assert (out/'emitted.ops').read_bytes()==lzma.decompress((candidate.parent/'circuit.ops.xz').read_bytes())
    assert json.loads((out/'independent.json').read_text())['status']=='PASS'
    assert json.loads((out/'interface.json').read_text())['status']=='PASS'
    assert verify_manifest()==manifest_hash
    result={'status':'PASS','manifest_sha256':manifest_hash,'source_sha256':sh(candidate),'emitted_sha256':sh(out/'emitted.ops'),'official_report_sha256':sh(out/'official/report.json'),'independent_report_sha256':sh(out/'independent.json'),'interface_report_sha256':sh(out/'interface.json'),'scope':'Fresh official shots, 837822 selected strict cases and exact changed-interface proof. Not a full-coordinate/all-accumulator task theorem.'}
    (out/'binding.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
