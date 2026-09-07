# GAP-6 repair record — writer instrument contract repair, Run-2 package freeze

Status: tooling amendment executed 2026-09-07 under the researcher's GAP-6 repair approval.
Companion to `GAP6_writer_instrument_contract_audit.md` (`a5ac0169…`). No writer session
was started at this gate.

## Run 1 stands

Commit `4d5e4db`, anchor `2145816f…`, validator report `8039a41b…`, gate verdict
`357e241e…`, terminal note `0949cef4…` are retained unaltered. Formal mark:
**WRITER_INSTRUMENT_CONTRACT_FAILURE**. Run 1 enters no DS/VO/UR identification result.
The Run-1 writer-visible package is preserved byte-for-byte at
`writer_handoff/run1_writer_package/` (renamed, gitignored; 58/58 against
`SHA256SUMS_WRITER_PACKAGE` with the path substituted). The Run-1 package audit report is
preserved as `writer_package_audit_report_RUN1.json` (`d8a4c826…`).

## Repair applied — exactly the frozen diff, nothing else

- Repair source: `GAP6_proposed_repair.diff`, sha256
  `cd6ae5f9959b26c0f1bee72fe3e92cbb487cb13bd161df8c18d3a8ea928af482` (verified before use).
- Target: the `WRITER_INSTRUCTIONS` constant in `build_study3_writer_handoff.py`, §4 only.
  Two insertions: (1) `edits[].action` is exactly `"removed"` or `"rewritten"`; (2) each of
  the five prose fields must be a non-empty string in every task, template `""` values are
  placeholders. No other wording changed.
- Byte-for-byte check: `patch(run1 INSTRUCTIONS.md, frozen diff)` == rebuilt
  `INSTRUCTIONS.md` — IDENTICAL.
- `INSTRUCTIONS.md` old `260a925e9ee3972efe7df285aab6445fb9a8bfef84aa1c0a7f45cdb9da51add3`
  → new `93ccaf5c4c1bdfa80c5564d8a9325d7b2d2d638745f5c9a5a2963b5a64e8e504`.
- `build_study3_writer_handoff.py` old `4c470fcd…` → new `46d57a59…` (re-pinned in
  `SHA256SUMS_TOOLING`, 27 entries incl. the new `audit_run2_package_diff.py`).

Untouched: validator, gate, scorer, template schema, constraints C, task/case content,
eligibility set, sealed key, startup prompt.

## Rebuild and checks

Rebuilt from the same frozen `eligibility_study3.json` (`a9db938b…`) with the frozen
builder seed; the build is deterministic.

| check | result |
|---|---|
| `study3_tooling_selftest.py` | 63/63 |
| `dataflow_audit.py` | PASSED |
| `test_resubmission_gate_study3.py` | 22/22 |
| `gap3_scope_audit.py` | results hash unchanged `d256f223…` |
| `audit_writer_package.py` | 15/15 (`writer_package_audit_report.json` `63a2b510…`) |
| `audit_run2_package_diff.py` | ONLY_LICENSED_DIFFERENCES (`run2_package_diff_audit.json`) |

Run-2 − Run-1 writer-visible package: 55 files each; added 0, removed 0, changed 1
(`INSTRUCTIONS.md`, equal to patch of Run-1); 53 task files hash-identical;
`output_template.json` identical `9eae55df…`; sealed key identical `3c9fc292…` → same 53
tasks, same W-id mapping, membership identical to the confirmatory eligible set.

New manifest: `SHA256SUMS_WRITER_PACKAGE_RUN2` (61 entries). `SHA256SUMS_WRITER_PACKAGE`
remains the Run-1 manifest.

Pre-existing observation, not caused by this gate: `SHA256SUMS_GAP3` (commit 45ffb8e) pins
pre-Amendment-2 bytes of `audit_baseline_packets.py` and `baseline_packet_audit_report.json`;
both were amended at 9bac069/5f823ed and are pinned at their current hashes in later
frozen sums. Both files are unmodified at HEAD. Left as is.

## Epistemic status of Writer Run 2 — frozen now, before any Run 2 exists

If a fresh Writer Run 2 is later approved:

**Writer Run 2 = post-failure, instrument-repaired replication of the constructive writer
procedure.** It is not the original preregistered writer run. The paper must disclose
together: Run 1's mechanical terminal state (UNREPAIRABLE_FIRST_SUBMISSION); GAP-6's two
ABSENT findings; that the repair was decided after seeing Run-1 mechanical issue codes and
counts; that the repair used no candidate substantive content; that Run 2 uses the same
53-task confirmatory set; that all subsequent substantive Study-3 results come from the
repaired instrument. Run 1 is never hidden from the research history.

## Run-2 contamination boundary — frozen now

Run 2 requires a new fresh isolated writer session that sees only the repaired
writer-visible package (`SHA256SUMS_WRITER_PACKAGE_RUN2`) and the frozen startup prompt
approved for Run 2. It must not see: the Run-1 submission or candidate content, the Run-1
validator report or issue counts, GAP-6 audit/history, any "what went wrong last time"
note, baseline judgments, DS/VO/UR, qualifying IDs, or other outcome information.

## Stop

This gate ends at the freeze. Writer Run 2 is not launched.
