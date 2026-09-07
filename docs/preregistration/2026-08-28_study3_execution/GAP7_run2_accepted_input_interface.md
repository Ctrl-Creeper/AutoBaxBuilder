# GAP-7 — Writer Run-2 accepted-input interface amendment

Status: tooling amendment executed 2026-09-07 after Writer Run 2 reached its frozen
`ACCEPT_FIRST_RUN2` mechanical terminal state and before any S-prime packet was built.
No verifier session, scorer execution, DS derivation, VO procedure, or candidate-content
inspection occurred in this gate.

## Trigger and authoritative input

The frozen S-prime builder and the accepted branch of the frozen scorer still named the
pre-GAP-6 interface: `SHA256SUMS_WRITER_FROZEN` and
`study3_writer_ACCEPTED.json`. Writer Run 1 permanently ended as
`WRITER_INSTRUMENT_CONTRACT_FAILURE`, so neither old path can be a constructive input.

The sole constructive writer input is now fixed to:

- artifact: `writer_handoff/submissions/writer_output_ACCEPT_FIRST_RUN2.json`
- manifest: `writer_handoff/SHA256SUMS_WRITER_FROZEN_RUN2`
- sha256: `f2b0e73ab1d8b5efcb22bb53c2b8d026446994992195d9b55b483d8de593b49e`

`run2_writer_input.py` implements this interface with constants and a zero-argument loader.
It does not accept a path, scan a directory, choose the newest file, fall back to an
existing submission, or name a Run-1 candidate. Before parsing JSON, it requires both the
manifest entry and the artifact bytes to equal the fixed hash; absence or mismatch is a
hard stop.

## Minimal tooling change

- `build_study3_sprime_packets.py`: old `d5bc365bb33ee4e3d9d5036ba09e7fa095fe8efcfe0c5673f11bb428ed460715`
  to new `f60f0b82a89ec301de95b8ff6dd8c39ed62e35e0a521338e3cc765cb0b546cf5`.
  Only its accepted-input dependency and corresponding key provenance hash changed; task
  selection, candidate-to-record construction, case loading, mapping, schema, seeds, and
  presentation call are unchanged.
- `score_study3.py`: old `b824be810c9d3b6bd3fc583edcf1ca7f3caf7650557c5bf8f4712ea6fcde73b6`
  to new `2425c8d10938b9828a2bca625366483408ec69e28eb2a412e6db809bb48dd8db`.
  Its accepted path now requires the same fixed loader. The GAP-5 unrepairable branch is
  unchanged. `cp_interval`, `map_ds_to_baseline`, `classify`, and `score` remain
  byte-identical at function-source level and retain their synthetic behavior fixtures.
- `README.md`: the obsolete accepted-path line is replaced by the Run-2 artifact and
  manifest names. Historical GAP-5 and Run-1 records remain byte-identical.
- `dataflow_audit.py`: the new loader is scanned as execution code and the allowlist now
  permits builder/scorer to import it. GAP-7 checks require the exact Run-2 source and bar
  Run-1 candidate, validator-report, baseline-judgment, eligibility-detail, prior-study,
  and outcome paths from the construction interface.

## Seed clarification

No seed, seed slice, task mapping, or packet logic changed. The frozen table remains:

- one shared `sprime_task_order` slice `[32:40]`, producing the shared anonymous task
  mapping fingerprint `f8c615689c16c53f913706fc7f6a72fbaa39dfd4378f474492739ea7df83ee5f`;
- independent `sprime_run1_cases` `[40:48]` and `sprime_run2_cases` `[48:56]`, producing
  case-order fingerprints `8025a077…` and `49a31293…` respectively.

This is the frozen design: both runs share anonymous task mapping/order and use independent
case permutations. No second task-order seed is created or derived.

## Mechanical evidence

`test_gap7_run2_writer_input.py` carries 15 focused checks: old-path refusal, missing-file
refusal, artifact-hash refusal, manifest-hash refusal, no caller-selected path, exact Run-2
acceptance, 53-task membership, frozen-case coverage, unchanged seed table, mapping and
both case-order fingerprints, semantic-payload equality, and byte/behavior invariance of
the scorer's substantive functions.

At amendment validation:

- GAP-7 fixtures: 15/15;
- existing tooling selftest: 63/63;
- Amendment-3 gate fixtures: 22/22;
- writer package audit: 15/15;
- Run1-vs-Run2 package diff audit: `ONLY_LICENSED_DIFFERENCES`;
- data-flow audit: passed;
- frozen protocol/frame consistency: passed.

## Stop

This gate ends at tooling freeze. No `sprime/` package, verifier isolation, submission,
scoring artifact, or prospective outcome is created.
