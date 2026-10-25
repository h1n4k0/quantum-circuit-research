#!/usr/bin/env python3
"""Verify the published initial-001 bytes; do not run scientific code."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path


def digest(kind, data):
    return hashlib.sha1(kind.encode() + b' ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('repository', type=Path)
    ap.add_argument('--output', required=True, type=Path)
    a = ap.parse_args()
    root, out = a.repository.resolve(), a.output.resolve()
    assert root.is_dir()
    assert not out.exists(), 'Refuse to overwrite an existing result'
    assert root not in out.parents and out != root, 'Write the result outside the repository'
    assert out.parent.is_dir(), 'Output parent must already exist'
    here = Path(__file__).resolve().parent
    manifest_path = here / 'initial_identity.json'
    m = json.loads(manifest_path.read_text())
    assert len(m['files']) == 27
    entries = {}
    xz = []
    for row in m['files']:
        p = Path(row['path'])
        assert not p.is_absolute() and '..' not in p.parts
        assert row['path'] not in entries
        q = root / p
        assert q.is_file() and not q.is_symlink()
        assert q.resolve().is_relative_to(root)
        b = q.read_bytes()
        assert len(b) == row['bytes'], row['path']
        assert hashlib.sha256(b).hexdigest() == row['sha256'], row['path']
        assert digest('blob', b) == row['git_blob_sha1'], row['path']
        entries[row['path']] = row
        if q.suffix == '.xz':
            raw = lzma.decompress(b)
            xz.append({'path':row['path'], 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()})
    def tree(prefix):
        direct = {}
        for path, row in entries.items():
            if not path.startswith(prefix):
                continue
            tail = path[len(prefix):]
            name, sep, rest = tail.partition('/')
            if sep:
                direct[name] = None
            else:
                direct[name] = row['git_blob_sha1']
        records = []
        for name, sha in direct.items():
            if sha is None:
                sha = tree(prefix + name + '/')
                mode, key = b'40000', name.encode() + b'/'
            else:
                mode, key = b'100644', name.encode()
            records.append((key, mode + b' ' + name.encode() + b'\0' + bytes.fromhex(sha)))
        return digest('tree', b''.join(data for _, data in sorted(records)))
    actual_tree = tree('')
    assert actual_tree == m['git_tree']
    checked = {}
    for name in ['PUBLICATION_MANIFEST.json', 'initial-001/MANIFEST.json']:
        source = root / name
        sub = json.loads(source.read_text())
        for p, expected in sub['files'].items():
            q = source.parent / p
            assert q.resolve().is_relative_to(root)
            assert hashlib.sha256(q.read_bytes()).hexdigest() == expected, p
        checked[name] = len(sub['files'])
    result = {
        'status':'PASS',
        'scope':'Published-file identity and compressed-stream integrity only; no circuit execution or new correctness proof.',
        'source_commit':m['source_commit'], 'git_tree':actual_tree,
        'files_checked':len(entries), 'bytes_checked':sum(r['bytes'] for r in entries.values()),
        'original_sha256_manifest_entries_checked':checked, 'xz_integrity':xz,
        'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'identity_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    }
    with out.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='xz_integrity'}, indent=2))


if __name__ == '__main__':
    main()
