# HHL full-domain numerical certificate — 25 October 2026

[Reproduction package and analytic argument](../experiments/20261025-hhl-integer-certificate/README.md)
and [independent review](../independent-review/20261025-hhl-integer-certificate/review.json).

The preserved HHL octave-tensor source is unchanged at **1206 logical Toffoli /
115 qubits**. The improvement here is evidence, not another resource reduction.

An independently written integer datapath and directed Q60 arcsine calculation
cover every **2,031,616** legal numerical input. The maximum real-angle error is
bounded above by **114661270226 / 2^60 radians**, approximately
**9.9452798623e-8**, below the unchanged `1e-7` target. Every rounded real ideal
is uniquely enclosed; maximum integer error is 427 inside the inclusive
429-unit contract. All independently reconstructed addends match the pinned
upstream model, checked separately after the numerical certificate.

The positive-series remainder, rounding directions, scales, source/constants
pins and integer-language assumptions are documented. Full-domain UBSan replay
and mutation tests pass. A separate reviewer reran the complete certificate,
checked the analytic argument, and compared 819 selected intervals against
a direct 48-term exact-rational sum and tail bound. That selected-input check
is not a second exhaustive independent census.

Fresh replay of the existing gate package and baselines also passes, but the
71,424 selected gate tests and suffix proof retain their previous scope. This
is **not** a new complete all-input/all-accumulator gate-level theorem, hardware
experiment or global-optimality result. Earlier unavailable sources are not
claimed as restored.

The generated 48,758,784-byte numerical record file is reproducible rather
than duplicated in Git. Its SHA-256 is
`ce5838584fc1ae454acd54c9e4e2d5df69f91c2018b7ac0efe7cdfcc647a37e8`.
Existing attribution and licensing remain unchanged.
