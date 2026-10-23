#!/usr/bin/env python3
"""Confirm the candidate changes only the forward lookup plus its helper/plan.
Not a semantic proof of the replacement: see the separate actual-stream checker.
"""
import argparse,ast,hashlib,json
from pathlib import Path
BASE='ce40b21cfc219816724dcf0ea47c03e0add6f685d6accd5871ff3685fe596b3f'
CAND='1379ef3398d3ac735bee2d4c4c4c045b77cce0500db506d91163a6fbfcc11cb7'
def normalize(path,new):
    t=ast.parse(path.read_text())
    # The embedded helper carries a no-op top-level documentation string.
    t.body=[n for n in t.body if not(isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))]
    if new:
        remove=[n for n in t.body if isinstance(n,ast.FunctionDef)and n.name=='partial_cache_lookup' or isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='PARTIAL_CACHE_PLAN'for x in n.targets)]
        assert len(remove)==2;t.body=[n for n in t.body if n not in remove]
    build=[n for n in t.body if isinstance(n,ast.FunctionDef)and n.name=='build'];assert len(build)==1
    blocks=[n for n in ast.walk(build[0])if isinstance(n,ast.With)and len(n.items)==1 and isinstance(n.items[0].context_expr,ast.Call)and n.items[0].context_expr.args and isinstance(n.items[0].context_expr.args[0],ast.Constant)and n.items[0].context_expr.args[0].value=='qrom/setup'];assert len(blocks)==1
    body=blocks[0].body;cuts=[j for j,n in enumerate(body)if isinstance(n,ast.FunctionDef)and n.name=='load_leaf'];assert len(cuts)==1
    blocks[0].body=body[:cuts[0]+1]
    return ast.dump(t,include_attributes=False)
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
assert hashlib.sha256(a.baseline.read_bytes()).hexdigest()==BASE
assert hashlib.sha256(a.candidate.read_bytes()).hexdigest()==CAND
assert normalize(a.baseline,False)==normalize(a.candidate,True)
a.output.write_text(json.dumps({'status':'PASS','baseline_sha256':BASE,'candidate_sha256':CAND,'scope':'Executable AST outside the forward-lookup replacement and its two new top-level helper/plan declarations is identical. Numerical fitting, arithmetic and phase erase are unchanged. This is not the replacement semantic proof.'},indent=2)+'\n')
