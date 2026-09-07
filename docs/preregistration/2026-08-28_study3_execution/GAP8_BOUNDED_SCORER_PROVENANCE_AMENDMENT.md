# GAP-8 - Bounded scorer provenance amendment

Date: 2026-09-07 (Asia/Taipei)

Status: frozen implementation record. This amendment changes only the final scorer's
terminal/provenance resolution. The final scorer was not run, `results_study3.json` was not
created, and no L0/L1/L2 result was computed in this gate.

Implementation base: commit `dd8e35fd54ef0897440c89751f2cd28e251c7739`.

Authorization: `GAP8_SCORER_TERMINAL_STATE_AUDIT.md`, SHA256
`4c1ed4494f7eefddf42a11bad69224f20791a89f1bd1616e510ece81077b520b`, ruling
`BOUNDED_PROVENANCE_AMENDMENT_AUTHORIZED`.

## Exact interface change

The old existence-only terminal-resolution block in `main()` (pre-amendment lines 158-185)
had SHA256 `ac8c82dcf0fa357d520fa76a12eafac712725393c9d29b6dcd070f282e8efa1d`
over those exact source lines. It is replaced by a zero-argument
`resolve_terminal_state() -> str` interface. The new function source has SHA256
`455ddbe09a53002b109521bcab198c9b9ff3b98a3d24134b3847995fdb87e0d1`
under `inspect.getsource()`.

The resolver has exactly two recognized returns:

- `FORMAL_RUN2_ACCEPTED`: the exact retained Run-1 terminal artifact, its GAP-6
  `WRITER_INSTRUMENT_CONTRACT_FAILURE` disposition, the exact Run-2
  `ACCEPT_FIRST_RUN2` terminal and accepted input, the frozen Run-2 S-prime/DS path, and
  the frozen VO-STRUCT path all coexist and pass their fixed hash/status/provenance pins.
- `FORMAL_PROCEDURE_INVALID`: the original gate-only GAP-5 terminal path exists without
  any post-Run-1 provenance marker. Its pre-existing scorer branch and procedure-invalid
  semantics remain unchanged.

The resolver accepts no path or state parameter, performs no directory/artifact-discovery
scan, chooses no latest file, has no fallback, and reads no task outcome in order to select a branch. Missing,
mismatched, partial, contradictory, or unknown terminal combinations are hard stops.

The formal accepted branch remains uniquely bound to
`writer_handoff/submissions/writer_output_ACCEPT_FIRST_RUN2.json`, SHA256
`f2b0e73ab1d8b5efcb22bb53c2b8d026446994992195d9b55b483d8de593b49e`.
The historical Run-1 `GATE_UNREPAIRABLE_FROZEN.json` remains byte-identical at SHA256
`357e241ea030ee598f8a091a4f9dacc2947f1f5de9249a9f1ce189cecf19f4c4`; it was not
deleted, moved, renamed, or modified.

## Scorer and substantive identity

| Artifact | Before | After |
|---|---|---|
| `score_study3.py` | `2425c8d10938b9828a2bca625366483408ec69e28eb2a412e6db809bb48dd8db` | `0ed4fd477d233881c699f2b497a03e79e5358ad681c294cd0feae5e94a53b415` |

The four substantive scorer functions are source-identical to the authorized pre-amendment
boundary:

| Function | SHA256 |
|---|---|
| `cp_interval` | `7525022292ad3693b063b5b9a814a3705330d1c3abc3f130ffd0844dd52bcf4a` |
| `map_ds_to_baseline` | `0d7659e562c868dd217f9129a9c568d9f9444acbb95e2d393b917feeb3456b74` |
| `classify` | `d7dd69b6e933f229904c136737c470a68253a823aa2a791331322f3e3a0f4aff` |
| `score` | `51e2e4cdb394a8a07506309bd9c1cf0bdb82b5182f8da3979345ef88fc3582e6` |

No DS/VO/UR rule, denominator, L0 equation, L1 interval, L2 sensitivity, overlap hard-stop,
VO handling, VO-DEFECT disposition, or formal procedure-invalid scoring behavior changed.

## TDD fixtures and verification

The RED fixture reproduced the old scorer's erroneous hard stop for the legally frozen
historical Run-1 plus formal Run-2 coexistence state. After the bounded resolver patch:

- GAP-8 terminal-state fixtures: 15 passed, 0 failed.
- GAP-7 Run-2 input fixtures: 15 passed, 0 failed.
- Amendment-3 resubmission fixtures: 22 passed, 0 failed.
- Existing synthetic tooling self-test: 63 passed, 0 failed.
- Data-flow audit: 36 passed, 0 failed.
- Protocol consistency check: 38 passed, 0 failed.

Direct invocation of the resolver in the frozen repository returned
`FORMAL_RUN2_ACCEPTED`. No call to `score_study3.main()` occurred.

## Data-flow boundary

Terminal resolution is limited to fixed Run-1 terminal provenance, GAP-6 disposition,
Run-2 terminal/accepted provenance, frozen S-prime/DS provenance, frozen VO-STRUCT
provenance, and their protocol/tool hashes. The accepted writer and DS/VO artifacts are
hash-checked without parsing their task-level substantive contents.

The resolver does not consume task-level DS identities, non-DS membership, verifier quotes,
candidate content, S-prime failure patterns, subgroup material, or outcome interpretation.
VO-DEFECT remains permanently closed.

## Execution disposition

`GAP8_BOUNDED_PROVENANCE_AMENDMENT_FROZEN`

There was no hard stop and no execution deviation. This freeze authorizes no scorer run;
final scoring remains a separate gate.
