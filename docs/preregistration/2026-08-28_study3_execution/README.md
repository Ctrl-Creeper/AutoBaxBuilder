# Study 3 — execution tooling (frozen before the formal draw)

Frozen inputs: protocol `548addbd…`, frame `ce8fd588…` (commit `75e7968`). Nothing here has
been run against them: the formal 764→90 draw is guarded behind `--approved-formal-draw`,
every builder behind `--approved-packet-build` / `--approved-writer-build`, and no formal
artifact (selection, packet, submission, derivation, result) exists at freeze.

## Execution order (each stage user-gated, per the frozen protocol)

1. `select_study3_sample.py --approved-formal-draw` → `selection_study3.json` (one SRSWOR
   draw, seed = int(protocol_sha[0:8],16); no redraw exists).
1b. `materialize_cases.py --approved-materialization` → sealed
   `sealed_materialization/FROZEN_CASE_MANIFEST.json` + public
   `case_materialization_public.json` (GAP-3 Amendment 2: the one authorized extraction,
   all 90 tasks; immutable; every later stage consumes this manifest and never re-extracts;
   the superseding invariant is packet case object ≡ manifest case object).
2. `build_study3_baseline_packets.py --approved-packet-build` → `baseline/{run1,run2}_package`
   (original S_t; the builder re-derives the draw and refuses on mismatch; cases from the
   frozen manifest only).
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
  unreachable from every stage that must be blind to them; the Amendment-3 gate can name
  only its three inputs (anchor, machine report, resubmission).
- `test_resubmission_gate_study3.py` — Amendment 3 clause-7 adversarial fixtures
  (synthetic only).

Resubmission gates: Interpretation Note 1 ruling 5's hard-stop fired **before any writer
output existed** — the pre-build mechanical check ordered with the writer-handoff approval
found the Round-2 gate implementation incompatible with the Study-3 writer schema (GAP-4).
Per the PI ruling, Amendment 3 (`AMENDMENT_3_study3_native_resubmission_gate.md`) reuses
the frozen Round-2 resubmission *discipline*, implemented prospectively against the frozen
Study-3 schema: `resubmission_gate_study3.py` (first submission = permanent substantive
anchor; A1–A3 allowlist frozen once, no A4 ever; structured issue-code interface to the
candidate validator; outcomes ACCEPT_FIRST / ACCEPT_REPAIRED / UNREPAIRABLE_FIRST_SUBMISSION).
An unrepairable first submission permanently stands as the formal writer output; downstream
handling per the protocol's own UR default and the open GAP-5 ruling (see Amendment 3).

The five mechanical parse decisions are ruled on in `INTERPRETATION_NOTE_1_parse_rulings.md`
(pre-draw): 1–4 accepted as frozen; VO-STRUCT predicates are sufficient-only certificate
rules (their failure never establishes separability — UR absent another frozen VO class);
5 clarified to the hard-stop semantics above.
