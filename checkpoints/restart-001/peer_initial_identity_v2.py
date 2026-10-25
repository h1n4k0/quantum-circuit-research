#!/usr/bin/env python3
"""Independent Git-tool and SHA-256 check of the 27-file published baseline.

This checks identity only. It does not import candidates or run circuit tests.
"""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('snapshot', type=Path)
    ap.add_argument('checkpoint', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    root, cp, out = a.snapshot.resolve(), a.checkpoint.resolve(), a.output.resolve()
    assert not out.exists()
    assert root not in out.parents and cp not in out.parents
    pub = json.loads((root/'PUBLICATION_MANIFEST.json').read_text())
    nested = json.loads((root/'initial-001/MANIFEST.json').read_text())
    expected = set(pub['files']) | {'PUBLICATION_MANIFEST.json'}
    actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    extras = sorted(actual - expected)
    assert expected <= actual and len(expected) == 27
    assert all('__pycache__' in Path(x).parts and x.endswith('.pyc') for x in extras), extras
    assert len(pub['files']) == 26 and len(nested['files']) == 19
    rows = {r['path']: r for r in json.loads((cp/'initial_identity.json').read_text())['files']}
    assert set(rows) == expected
    for name, digest in pub['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest
        assert subprocess.check_output(['sha256sum', str(root/name)], text=True).split()[0] == digest
    for name, digest in nested['files'].items():
        assert pub['files']['initial-001/'+name] == digest
    with tempfile.TemporaryDirectory(prefix='quantum-identity-peer-') as tmp:
        subprocess.run(['git','init','-q',tmp], check=True)
        for name in sorted(expected):
            source = root/name
            assert not source.is_symlink() and source.resolve().is_relative_to(root)
            raw = source.read_bytes()
            dest = Path(tmp)/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(raw)
            dest.chmod(0o644)
            blob = subprocess.check_output(['git','-C',tmp,'hash-object','--stdin'],input=raw).decode().strip()
            assert blob == rows[name]['git_blob_sha1']
            assert len(raw) == rows[name]['bytes']
            assert hashlib.sha256(raw).hexdigest() == rows[name]['sha256']
        subprocess.run(['git','-c','core.autocrlf=false','-C',tmp,'add','-f','--',*sorted(expected)],check=True)
        tree = subprocess.check_output(['git','-C',tmp,'write-tree'],text=True).strip()
    manifest = json.loads((cp/'initial_identity.json').read_text())
    assert tree == manifest['git_tree']
    rerun = out.with_name(out.stem+'_runner.json')
    assert not rerun.exists()
    subprocess.run(['python',str(cp/'verify_initial_identity.py'),str(root),'--output',str(rerun)],check=True)
    fresh = json.loads(rerun.read_text())
    recorded = json.loads((cp/'result.json').read_text())
    assert fresh == recorded
    report = {
        'status':'PASS', 'scope':'Original 27-file byte identity, Git tree, two manifests, unchanged identity-runner replay; no fresh scientific execution.',
        'source_commit':manifest['source_commit'], 'git_tree':tree,
        'file_count':27, 'publication_manifest_entries':26, 'nested_manifest_entries':19,
        'independent_methods':['sha256sum and hashlib for published entries','Git hash-object for all 27 blobs','Git write-tree on an isolated exact 27-file tree'],
        'review':['Original allowlist deliberately excludes subsequent checkpoints.','Original manifest and payload mutations are caught by pinned bytes.','No candidate imports; XZ decompression is integrity evidence, not circuit verification.','Output must be new and outside the inspected checkout.'],
        'checkpoint_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(cp.iterdir()) if p.is_file()},
        'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'fresh_runner_result_sha256':hashlib.sha256(rerun.read_bytes()).hexdigest(),
        'fresh_runner_equals_recorded':True,
        'ignored_generated_bytecode_not_in_original_allowlist':extras,
    }
    with out.open('x') as f: json.dump(report,f,indent=2); f.write('\n')
    print(json.dumps(report,indent=2))

if __name__ == '__main__': main()
