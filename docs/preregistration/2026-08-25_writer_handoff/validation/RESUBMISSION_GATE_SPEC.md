# Resubmission identity gate — specification

Frozen before the fix request goes back to the writer.

## What this resubmission is

A **provenance-completion resubmission**, not a second round of authoring. The first submission was
not accepted for two mechanical reasons: `edits[].field` used display-cased names, and clause-level
changes were left undeclared. The remedy is to complete the record of edits already made.

## Why a byte-identity constraint is necessary

The writer now knows what the validator's H9 looks for. Without this gate they could satisfy it by
rewording a candidate to need fewer declarations — which would let validator feedback reach the
specifications, the very material the two blinded coding runs are meant to judge untouched. The
constraint is enforced rather than requested.

## Allowlist — the only permitted changes

| | change |
|---|---|
| A1 | `edits[].field` normalised to the schema's lowercase key |
| A2 | new entries **appended** to `edits[]` |
| A3 | a structural repair to a `failure` object that violates the schema, keeping its code |

No `failure` object in the baseline is schema-invalid, so A3 is expected to go unused.

## Frozen — any difference is a HARD FAIL

Every character of every candidate field; every existing edit entry's body and its position;
`sufficiency_evidence`; `notes`; `failure` content; the task id set and count; `writer_id`;
`schema_version`; and the absence of any key not in the baseline.

In particular: a validator result is never grounds for reinterpreting a task, re-opening a task for
new specification design, or "improving" prose that H9 flagged. A resubmission never triggers
replacement and never alters the 90-task manifest.

## Checks

- one-to-one correspondence of blinded ids with the baseline, same count, same set
- candidate spec SHA256 identical per task, over the five fields, byte-exact
- failure records identical unless the baseline one violated the schema
- existing edit bodies unchanged and in order, compared with the field name lowercased so that A1 is
  invisible to the comparison; appends allowed
- no key outside the baseline's
- a machine-readable delta, with every change classified as allowlisted or not

## Output — `resubmission_delta.json`

Per task: `casing_fixed`, `provenance_added`, `spec_hash_before`, `spec_hash_after`,
`non_allowlisted[]`. Totals across the submission. Any non-empty `non_allowlisted` is a hard failure.

## Acceptance

**Both** must pass, in this order:

```
resubmission_identity_gate.py  →  validate_writer_output.py  →  freeze submission hash
```

The identity gate governs what may have changed since the baseline. The frozen writer validator
governs whether the contract is now met. Neither substitutes for the other, and neither judges
whether a specification is any good — that remains the construct the coding runs measure.

## Self-test

Positive: casing corrected and declarations appended, accepted. An unchanged resubmission is also
accepted, because a no-op is inside the allowlist — it is the writer validator, not this gate, that
still rejects it. Fourteen negatives, each one further change: prose edited, prose shortened, task
removed, task added, existing edit modified, removed or reordered, notes changed, sufficiency
evidence changed, failure reinterpreted, failure code swapped, schema version changed, writer id
changed, unexpected key.
