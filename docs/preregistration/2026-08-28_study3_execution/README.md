# Study 3 — execution tooling (frozen before the formal draw)

Frozen inputs: protocol `548addbd…`, frame `ce8fd588…` (commit `75e7968`). Nothing here has
been run against them: the formal 764→90 draw is guarded behind `--approved-formal-draw`,
every builder behind `--approved-packet-build` / `--approved-writer-build`, and no formal
artifact (selection, packet, submission, derivation, result) exists at freeze.

## Execution order (each stage user-gated, per the frozen protocol)

1. `select_study3_sample.py --approved-formal-draw` → `selection_study3.json` (one SRSWOR
   draw, seed = int(protocol_sha[0:8],16); no redraw exists).
2. `build_study3_baseline_packets.py --approved-packet-build` → `baseline/{run1,run2}_package`
   (original S_t; the builder re-derives the draw and refuses on mismatch).
3. Two fresh isolated coder sessions (STARTUP_PROMPT_CODER.txt), per-run
   `validate_study3_submission.py`, independent freeze into
   `submissions_baseline/{run1,run2}_baseline_FROZEN.json` + `SHA256SUMS_BASELINE_FROZEN`.
4. `derive_eligibility.py` → `eligibility_study3.json` (mechanical both-agree rule; m is a
   result; m = 0 branch prespecified).
5. `build_study3_writer_handoff.py --approved-writer-build` → `writer_handoff/writer_package`
   (eligible tasks only; STARTUP_PROMPT_WRITER.txt); `validate_study3_candidate.py`;
   freeze `writer_handoff/study3_writer_ACCEPTED.json` + `SHA256SUMS_WRITER_FROZEN`.
6. `build_study3_sprime_packets.py --approved-packet-build` → `sprime/{run1,run2}_package`;
   two fresh sessions (disjoint from baseline sessions), per-run validation, freeze into
   `submissions_sprime/` + `SHA256SUMS_SPRIME_FROZEN`.
7. `derive_ds.py` → `ds_derivation.json`; `vo_certificates.py` → `vo_certificates.json`
   (VO-DEFECT certificates, if any, live in `vo_defect/` with independent attestations).
8. `score_study3.py` → `results_study3.json` (DS∧VO = hard stop; sample identification
   region + two CP intervals + L2 sensitivity; nothing else).

## Frozen mechanical parse decisions

Documented in `study3_pins.py`'s docstring: case-level both-agree eligibility; per-run DS
profile; def-line parameter extraction (Round-2 rule); the four VO-STRUCT immutable-carrier
predicates; protocol-hash seed slices. Each implements frozen protocol wording with frozen
precedent; none introduces a rule.

## Verification

- `study3_tooling_selftest.py` — 53 checks on synthetic fixtures only (writes
  `selftest_open_trace.json`).
- `dataflow_audit.py` — per-file banned literals, AST import allowlists, runtime open
  trace: Study-1 results/judgements cannot enter selection, baseline, eligibility, or
  scoring; Round-2 J2/J3 tokens may not appear in execution code; writer artifacts are
  unreachable from every stage that must be blind to them.

Resubmission gates, if a writer resubmission is ever needed, are inherited from the frozen
Round-2 gate discipline (`2026-08-25_writer_handoff/validation/`), per protocol §5; any
shape mismatch at that point is a recorded deviation, not an improvised rule.
