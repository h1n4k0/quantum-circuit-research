# Identity peer and a refused preflight

`peer_initial_identity_v2.py` independently uses `sha256sum`, Git
`hash-object`, and Git `write-tree`, then replays the unchanged identity
runner. Its recorded result is `initial_identity_peer_v2.json`.
No candidate circuit is executed by this peer.

The first peer required the entire recovered directory to contain exactly
27 files. A scientific audit import generated a Python bytecode cache, so
that preflight refused to produce a success report. The original 27 file
bytes were unchanged. The original script and concise failure record are
retained; v2 permits only explicitly identified `__pycache__/*.pyc` extras
and excludes them from the original Git tree.

Unlike the primary allowlist checker, this exact-snapshot peer must be
given an export of the original commit, not a later checkout containing
new checkpoints. From a clone with the original commit available:

```sh
mkdir /tmp/quantum-initial-export-new
git archive b6e0080c1eb45e2c3c62602527bb6f325c096342 | tar -x -C /tmp/quantum-initial-export-new
python checkpoints/restart-001/peer_initial_identity_v2.py \
  /tmp/quantum-initial-export-new checkpoints/restart-001 \
  --output /tmp/quantum-identity-peer-new.json
```

Choose unused paths. The peer requires Git and `sha256sum` in addition
to Python. The primary checker requires only the Python standard library.
The peer result binds the original four checkpoint files; the complete
publication payload is separately bound by `MANIFEST.json`.
