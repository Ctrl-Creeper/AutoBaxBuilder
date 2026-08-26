# Amendment record — resubmission identity gate v2 → v3

| | |
|---|---|
| gate v1 | `4b55454cbc36357ad0d96694aeaa0d2c0288f0a177c4c9a6518825d4cdeef68f` — **permanently retained** |
| gate v2 | `524b660e669333c265ef5f360ad1713085f7d46d35b7b274a141ea80ca9c63bf` — **permanently retained** |
| gate v3 | see `SHA256SUMS_RESUBMISSION_V3` |
| frozen writer validator | `e948ffffc84f1c24ea0e5d1204b1c5e96c67b3dfe2ac3aa897d3d1aab2c45cc9` — **unchanged** |
| identity baseline (spec anchor) | `1411381da1527a4d65fa849c953fe3d79c07076f3e7c579065974145f3bf37c1` |

## 1. What triggered v3: a provable gate defect, not an unwelcome result

A4.2 carried a secondary guard requiring that the text preceding the ellipsis in an abbreviated
quotation survive verbatim in its expansion. That guard assumed abbreviation is always **truncation**.

On W54 edit 2 the writer's abbreviation was a **paraphrase**:

| | |
|---|---|
| abbreviated quotation | `- hashlib: provides cryptographic hash functions...` |
| frozen input actually reads | `- hashlib: The 'hashlib' module provides a set of cryptographic hash functions such as: {…}` |

`provides cryptographic hash functions` is not a contiguous substring of the frozen input — it says
`provides **a set of** cryptographic hash functions`. So **no string exists** that satisfies both
A4.2's own requirement (exact presence in the frozen input) and the guard (contains the old fragment).
The gate demanded a correction that could not be written. That is a defect in the gate, demonstrable
without reference to any outcome, and it is what v3 removes.

## 2. What was removed, and what was not

**Removed:** the fragment-survival guard inside A4.2, six lines. Nothing else. The full diff between
v2 and v3 is that block, the docstring, and the version label.

**Unchanged:** the set of objects that may be modified is exactly as in v2. A4.1, A4.3, A1, A2 and A3
are untouched. The frozen writer validator is untouched.

## 3. A4.2 as it now stands

A corrected `original` must:

- belong to the **same blinded task**;
- belong to the **same field** — retargeting is a hard failure;
- be present **complete and verbatim** inside that field of the frozen writer input;
- and belong to an entry the frozen validator itself flagged as untraceable.

## 4. The candidate specifications remain frozen

Per task, sha256 over the five candidate fields must equal both the immediate predecessor's and the
original anchor's. Checked before anything else, overridden by no allowlist entry, unchanged since v1.
**90 of 90 matched** on the submission this amendment was written against.

## 5. Substitution probes — and a correction to an earlier claim

The removed guard was the only rule aimed specifically at substitution, so before freezing v3 the
question was tested rather than argued. Both probes use text that genuinely exists in the frozen
input, so neither is caught by A4.2's exact-presence condition.

| probe | gate v3 | frozen validator | pipeline |
|---|---|---|---|
| **S1** quotation swapped for another real clause in the **same** field | PASS | **BLOCKED** | blocked |
| **S2** quotation swapped for a real clause in a **different** field | **BLOCKED** | BLOCKED | blocked |

**Correction, recorded because it was asserted before it was tested.** It was claimed in discussion
that A4.2's verbatim matching "already blocks substitution with another clause". That is **false for
the same-field case**. A4.2 alone does not block S1; the gate passes it. What blocks S1 is the frozen
writer validator's undeclared-removal check: swapping a declaration leaves the clause it used to
cover undeclared, and that is caught. The protection is a property of the **pipeline**, not of the
gate, and it depends on a rule in an artefact this amendment does not touch.

No similarity heuristic was invented to close the gate-level hole. The hole is recorded here instead.

All thirteen negatives carried over from the v2 self-test remain blocked by gate v3, including
`quotation_substituted`.

## 6. Standing limitation

Gate v3 cannot, by itself, distinguish completing a quotation from swapping it for a different real
clause in the same field. Detection of that case rests entirely on the frozen writer validator. If
that validator's undeclared-removal check were ever weakened, this gate would not compensate.

## 7. Acceptance order

```
resubmission_identity_gate_v3.py  →  validate_writer_output.py  →  freeze accepted submission SHA256
```

Both must pass. Provenance repair ends there; no further gate version will be issued.
