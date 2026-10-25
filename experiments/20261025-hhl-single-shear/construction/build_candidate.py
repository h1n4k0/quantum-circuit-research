#!/usr/bin/env python3
"""Apply a screened invertible coordinate change only inside phase repair.
This constructor consumes exact-table plans; actual gates require verification.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
BASE='d854ac76c46919b83568c307767049b241c19655b84330ba1cfd2b713df09f37'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--screens',type=Path,nargs='+',required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 base=a.baseline.resolve();out=a.output.resolve()
 assert not out.exists()
 package=Path(__file__).resolve().parents[1]
 assert out!=package and package not in out.parents, 'Output inside constructor package'
 for p in (base,*base.parents,out,*out.parents):
  if p in (out,*out.parents):assert not any((p/n).exists() for n in ('MANIFEST.json','PUBLICATION_MANIFEST.json'))
 assert base not in out.parents
 source=(base/'circuit.py').read_text();assert hashlib.sha256(source.encode()).hexdigest()==BASE
 plan=json.loads((base/'phase_plan.json').read_text());selected=plan['plans'];changes=[]
 for screen in a.screens:
  report=json.loads(screen.read_text());assert report['status']=='EXACT_TABLE_SCREEN_ONLY'
  assert report['constants_sha256']==hashlib.sha256((base/'constants.json').read_bytes()).hexdigest()
  for candidate in report['best']:
   e=candidate['exponent'];old=selected[e-16]
   # Keep only strict nonlinear-feature improvements in this first candidate.
   if candidate['phase_products']<old['phase_products']:
    selected[e-16]=candidate;changes.append({'exponent':e,'before':old['phase_products'],'after':candidate['phase_products'],'shear':candidate['shear']})
 assert changes
 start='''        floor, n, pol = p["floor"], p["n"], p["polarity"]
'''
 replacement=start+'''        shear = p.get("shear")
        if shear:
            target, control = shear
            b.cx(XQ[floor + control], XQ[floor + target])
'''
 assert source.count(start)==1;source=source.replace(start,replacement)
 end='''    def octave_walk(e, ctrl=None):
'''
 replace='''        if shear:
            b.cx(XQ[floor + control], XQ[floor + target])

'''+end
 assert source.count(end)==1;source=source.replace(end,replace)
 source=source.replace('HHL candidate: exact per-octave split-monomial phase readout.','HHL candidate: exact split-monomial phase readout after local CX shears.')
 out.mkdir(parents=True)
 (out/'circuit.py').write_text(source);shutil.copyfile(base/'constants.json',out/'constants.json')
 newplan={'status':'EXACT_LOCAL_TABLES','construction':'per-octave split-monomial phase readout with local reversible CX basis changes','plans':selected,'baseline_source_sha256':BASE,'planned_phase_products':3+sum(p['phase_products'] for p in selected),'changes':changes}
 (out/'phase_plan.json').write_text(json.dumps(newplan,indent=2)+'\n')
 print(json.dumps({'changes':changes,'planned_phase_products':newplan['planned_phase_products'],'source_sha256':hashlib.sha256(source.encode()).hexdigest()},indent=2))
if __name__=='__main__':main()
