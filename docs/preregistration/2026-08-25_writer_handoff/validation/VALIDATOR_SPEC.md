# Writer-output validator — specification

Frozen before authoring begins. Any change to `validate_writer_output.py` after that point changes
its hash and invalidates acceptances made under it.

## What this validator is for, and what it must never do

It checks **delivery against a frozen contract**: that ninety candidates arrived, that each traces to
its frozen input, that nothing outside the editable fields moved, and that every difference between
original and candidate is declared.

It does **not** ask whether a candidate is functionally sufficient, whether it leaves the second case
list open, or whether it is a good rewrite. Those are the constructs the two blinded coding runs exist
to measure. A validator that decided them would be writing the study's result into the data-generating
process — an acceptance gate that only lets through specifications the tooling already believes are
correct guarantees the coders agree with the tooling.

The positive fixture is built to make this concrete: it copies the original prose through unchanged,
which is a poor rewrite by any reading, and the validator accepts it.

## Two tiers, enforced

| tier | on failure |
|---|---|
| **HARD** | Submission is not accepted. Exit 1. Returned to the writer as a submission-format or provenance error. |
| **DIAGNOSTIC** | Printed. Never acted on. Never changes the exit code. |

A diagnostic **may not** cause a task to be edited, dropped, replaced or re-authored. Diagnostics
exist so that an anomaly is visible in the record, not so that it can be corrected. The distinction
is enforced in code: diagnostics never reach the exit path.

## Hard invariants

| # | invariant |
|---|---|
| H1 | `schema_version` equals the frozen value; `writer_id` is non-empty |
| H2 | The package on disk still matches `writer_package_manifest.json` byte for byte, and the frozen selection file is unchanged — this is what establishes that the non-editable material (function name, signature, setup/preamble, List A, List B) did not move |
| H3 | Exactly the 90 frozen blinded ids are present; none missing, none unknown, none duplicated |
| H4 | Each task object has exactly the five contract keys — a missing key is an error, never a default filled in by tooling |
| H5 | `spec` has exactly the five editable prose fields; `security_policy` appears nowhere in it |
| H6 | No non-editable material is smuggled into `spec` (any extra key fails H5) |
| H7 | Every declared edit names an original prose field, a legal action, and quotes an `original` that is present verbatim in the frozen input |
| H8 | A `rewritten` edit's `replacement` appears in the candidate field; a `removed` edit carries no replacement |
| H9 | Every clause present in the original prose and absent from the candidate is covered by a declared edit — the converse of H7, so a silent deletion cannot pass |
| H10 | A `failure`, if present, carries exactly `code`/`at_case`/`detail` and a code from the frozen taxonomy |
| H11 | A failure never leaves the candidate empty — a failure code records what blocked the rewrite, it does not discharge the obligation to submit a best candidate |
| H12 | No coding-side classification vocabulary appears anywhere in a task record |

H3 and H11 together implement the rule that **a task may never be dropped and a failure never triggers
replacement**. The reserve list frozen at `e7ae0c1` admits mechanical construction failures only; a
writer failure code is not among them and none may be added now.

## Diagnostics

Candidate/original prose length ratio and its outliers; edits per task and how many tasks declared
none; count of empty editable fields; distribution of failure codes.

Each is a distributional observation about the submission. None is evidence about any task, and none
is grounds for touching one.

## Downstream obligation

On acceptance the validator prints the submission's SHA256. That hash is frozen and committed before
any packet is built.

**The packet builder consumes the frozen output as it stands.** It does not regenerate, normalise,
clean or repair a specification. A defect discovered at packet-build time is recorded as a defect;
it is not silently fixed, and it does not send the task back to the writer.

## Fixtures

- `fixtures/positive_submission.json` — 90 tasks, must be ACCEPTED.
- `fixtures/negative_mutations.json` — one mutation per hard invariant, each derived from the positive
  fixture by changing exactly one thing. Recorded as mutations rather than as fourteen near-identical
  copies, so that "exactly one change apart" is visible rather than asserted; `test_validate_writer_output.py`
  applies them deterministically.
- `test_validate_writer_output.py` — runs the positive fixture, every negative, and a tampered-package
  case in which a frozen signature line is altered after freezing.

Self-test at freezing: positive accepted, 13 negatives rejected, package tampering caught.

## Usage

```
python validate_writer_output.py <writer_output.json> [--package DIR] [--json OUT]
```

Exit 0 = accepted, 1 = not accepted.
