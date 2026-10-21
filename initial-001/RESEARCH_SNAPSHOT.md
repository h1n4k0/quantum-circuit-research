# Initial research snapshot

This is an early reproducible checkpoint, not a completed study or a claim
of a new general algorithm. Logical resource improvements are measured
against the released circuits in [Gu et al., arXiv:2610.22367v1](https://arxiv.org/abs/2610.22367).
The reference implementation is [andigu/uncompute](https://github.com/andigu/uncompute)
at commit `64b5a13aa249f1360846657392e6c66817b26d0f` (Apache-2.0).

| Task | Released Toffoli / peak qubits | Candidate | TQ reduction |
|---|---:|---:|---:|
| HHL angle | 1348 / 115 | 1273 / 115 | 5.56% |
| Coulomb inverse distance | 1140 / 142 | 1110 / 142 | 2.63% |

T means logical **Toffoli gates**, not T gates. TQ is Toffoli count times
peak logical qubits; it is not physical runtime. No hardware experiments
or physical error-correction estimates are claimed.

Classical outcome IDs increase from1040 to8902 for HHL, and1950 to2039
for Coulomb. The original TQ objective does not charge this classical
bookkeeping. HHL Clifford counts decrease56419 to14889; Coulomb7253 to6716.
Thus the improvement does not assert that every resource measure improves.

HHL keeps the numerical tables and arithmetic unchanged and reorganizes
measurement-phase repair using the actual leaf granularity and sparse
algebraic-normal-form monomials. Coulomb combines a regrouped exact squarer
with algebraic-normal-form lookup and phase repair. These are incremental
improvements to the released implementation; literature novelty remains
unassessed.

## Verification evidence and limits

Official unchanged graders accept both candidates, including output values,
restored inputs, ancillary cleanliness and phase on their sampled tests.
The reports retain the emitted-op SHA-256 hashes.

An independent research worker additionally ran:

* HHL: all 2,031,616 inputs through the unchanged integer datapath model;
  maximum unrounded angular error `9.9452798663e-8` radians. 71,424
  gate-level cases cover all 7,936 minimum-granularity selector classes,
  three within-block values and three accumulator carry regimes.
* Coulomb: an integer-only inverse-square-root rounding oracle for all
  195,075 positive squared distances. 837,822 gate-level cases cover every
  attainable squared distance (139,637), two coordinate orientations and
  three accumulator carry regimes. Maximum rounded-output error is32 units;
  the rigorous real-value bound `32.5/2^24 < 2e-6` follows.
* Both gate tests use the upstream strict affine phase ledger, which checks
  every measurement outcome for each tested basis input, not just sampled
  outcomes.

The worker, tests and Coulomb integer oracle are independent of the candidate
authors, but the simulator and HHL numerical model are upstream code. This
is not a formal proof of the entire circuit for every coordinate pair or
every possible accumulator value. No statevector or physical-device
simulation is asserted. Correctness contracts and accuracy are unchanged.

## Reproduce

Python3.10+ with NumPy and Click is sufficient for these tasks; a C compiler
can build the optional faster simulator. No LLM API or paid service is used.

```sh
git clone https://github.com/andigu/uncompute.git upstream
git -C upstream checkout 64b5a13aa249f1360846657392e6c66817b26d0f
mkdir -p upstream/tasks/hhl-angle/circuits/research-anf-v1
mkdir -p upstream/tasks/coulomb-potential/circuits/research-combined-v1
cp candidates/hhl/anf_v1/* upstream/tasks/hhl-angle/circuits/research-anf-v1/
cp candidates/coulomb/combined_v1/* upstream/tasks/coulomb-potential/circuits/research-combined-v1/
make -C upstream kernel
PYTHONPATH=upstream python upstream/tools/eval.py hhl-angle \
  --circuit upstream/tasks/hhl-angle/circuits/research-anf-v1/circuit.py \
  --out results/reproduced-hhl
PYTHONPATH=upstream python upstream/tools/eval.py coulomb-potential \
  --circuit upstream/tasks/coulomb-potential/circuits/research-combined-v1/circuit.py \
  --out results/reproduced-coulomb
python verification/audit_hhl_candidate.py \
  upstream/tasks/hhl-angle/circuits/research-anf-v1/circuit.py \
  --upstream upstream --output results/reproduced-hhl-independent.json
python verification/audit_coulomb_candidate.py \
  upstream/tasks/coulomb-potential/circuits/research-combined-v1/circuit.py \
  --upstream upstream --output results/reproduced-coulomb-independent.json
```

The complete upstream repository is not included. Published candidates are
modified versions of its Apache-2.0 source. Preserve `UPSTREAM_LICENSE` and
attribution when redistributing. No repository-wide license is assigned to original research contributions;
see `LICENSING.md` in the repository root.
