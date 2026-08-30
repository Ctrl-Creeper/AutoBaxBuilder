# Study-3 writer arm — terminal state record (2026-08-30)

Sequence executed exactly as frozen: writer completed 53/53 in a fresh isolated session
(inputs byte-verified untouched afterwards) → raw bytes saved → SHA256 →
FIRST_SUBMISSION_ANCHOR recorded → only then the frozen validator ran.

- FIRST_SUBMISSION_ANCHOR sha256
  2145816f8659544e1442e44e12ce4450063f15f4036a9a99638835ee7cf39c0d (permanent formal
  writer output, Amendment 3 clause 1 / GAP-5 clause 2)
- Frozen validator verdict: NOT ACCEPTED — 82 issues, exactly two machine codes:
  PROVENANCE_VALUE_INVALID ×45 (edits[].action value outside removed/rewritten),
  EMPTY_CANDIDATE_FIELD ×37 (an empty prose field in the shipped candidate).
- Amendment-3 gate verdict: UNREPAIRABLE_FIRST_SUBMISSION — neither code is in the
  frozen A1–A3 licensing map; both defects are substantive under the anchor rules
  (changing an edits action value, or authoring absent prose, would alter the
  substantive object). No A4 was created; gate, validator and writer instructions were
  not modified; no repair guidance went back to the writer. The gate's unrepairable
  branch is a pure function of (anchor, validator report); the --gate CLI argument was
  satisfied with the anchor path and its bytes were never read by that branch.
- No resubmission was solicited or exists.

Downstream is fixed by the pre-outcome GAP-5 ruling (Interpretation Note 2): all 53
tasks remain in m; none enters S′ verification; none can be DS; the independent
VO-STRUCT/VO-DEFECT certificate pathway remains; the remainder is UR; the scorer
routes via the frozen GATE_UNREPAIRABLE_FROZEN.json and reports
procedure_invalid_candidate = 53 as a procedure diagnostic.

## Instrument observation (recorded, not acted on)

Both failing codes plausibly trace to a contract-communication gap between two frozen
artifacts, discovered only now: the writer INSTRUCTIONS (§4) describe edits[] as
"{field, original, action, replacement, why} per clause removed or materially changed"
but never enumerate the validator's action vocabulary (removed/rewritten), and never
state that every prose field must be non-empty. The validator behaved exactly per its
frozen specification; the writer followed the instructions as written. Whether and how
this bears on the study is not decided here — no rule is invented post-output, and no
artifact was altered. Candidate substantive content was not read for this record; only
machine codes and counts.
