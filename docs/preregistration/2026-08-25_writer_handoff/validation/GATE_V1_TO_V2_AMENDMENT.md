# Amendment record — resubmission identity gate v1 → v2

| | |
|---|---|
| gate v1 | `4b55454cbc36357ad0d96694aeaa0d2c0288f0a177c4c9a6518825d4cdeef68f` — **retained, not overwritten, not rewritten** |
| gate v2 | `524b660e669333c265ef5f360ad1713085f7d46d35b7b274a141ea80ca9c63bf` |
| identity baseline (spec anchor) | `1411381da1527a4d65fa849c953fe3d79c07076f3e7c579065974145f3bf37c1` |
| previous submission (v2's comparison point) | `c7d69948f86a2b705031ece4835b833b319cc1145750232a90a0cb65c6d0978a` |
| frozen validator report that triggered this | `3b6038d09fad94b47b92accc30c6560afb131a1f52d4dbfd2ba6f2cfa954f583` |

## When, and why

The amendment was made **after the first resubmission had been frozen and scored**. The frozen writer
validator returned 54 hard failures on it, of two provenance-format kinds that v1's allowlist gave no
way to fix: v1 permits appending an entry or lowercasing its field, and both defects require
correcting an entry **in place**.

| type | count | tasks | validator message |
|---|---|---|---|
| flagged action | 37 | 37 | `action is rewritten but no replacement is given` |
| flagged quotation | 8 | 7 | `the quoted original is not present in the frozen … field` |
| consequent undeclared removal | 9 | 7 | `a clause of the original … is absent from the candidate with no edit declaring it` |

The third type is downstream of the second: an abbreviated quotation cannot cover the clause it was
meant to declare.

## This gate is not outcome-blind, and does not claim to be

v1 was written before any result was seen. **v2 was not.** It was authored with 54 validator failures
in view, and that is recorded here rather than glossed over. What follows from it is a restriction,
not a licence: an amendment written in sight of results may widen **metadata correction only**, and
may not touch research content. No reading of any specification, and no expectation about how any task
will later be coded, entered the design of A4.

## A4 — the exact scope added

Applies **only** to entries the frozen validator itself flagged. The gate reads the flagged set from
the frozen report and independently recomputes it, and refuses to run if the two disagree, so "the
validator determined it" is verified rather than asserted.

| rule | permitted | forbidden |
|---|---|---|
| **A4.1** action | `rewritten` → `removed`, only for a flagged-action entry | the reverse direction; any change to an unflagged entry |
| **A4.2** original | expanding an abbreviated quotation to the complete verbatim text, only for a flagged-quotation entry, and only if the new value exact-matches inside the frozen writer input | substituting a different clause; paraphrase; summary; any change to an unflagged entry |
| **A4.3** replacement | correcting the value for structural consistency with the entry's action, only for a flagged entry; a non-empty value must exact-match inside the frozen candidate | inventing text; any change to an unflagged entry |

Unchanged from v1: A1 field-name casing, A2 appends, A3 structural repair of a schema-invalid failure
object with its code preserved.

## Why A4 cannot reach the candidate text

The gate's **first and highest-priority** check, applied before anything else and unchanged from v1,
is a per-task SHA256 over the five candidate fields — compared against **both** the immediate
predecessor and the original anchor. Any difference is a hard failure and no allowlist entry
overrides it.

A4 operates entirely on the edit list, which is a *record of changes already made*. Relabelling an
action or completing a quotation alters the description of an edit, never the text the edit describes.
Additionally A4.2 requires the expanded quotation to exact-match the **frozen writer input**, and A4.3
requires a non-empty replacement to exact-match the **frozen candidate** — so both corrections can only
converge on material that already exists and is already frozen.

## Machine-checkable rules

| field | rule the gate enforces |
|---|---|
| every candidate field | per task, sha256(spec) equals sha256(prev.spec) and sha256(anchor.spec) |
| edit field name | equal to the predecessor's, case-insensitively |
| edit why | byte-identical |
| edit action | unchanged, or the entry is in the flagged-action set and the change is rewritten → removed |
| edit original | unchanged, or the entry is in the flagged-quotation set, the normalised new value is a substring of the normalised frozen input field, and a retained fragment of the abbreviation survives in the new value |
| edit replacement | unchanged, or the entry is flagged; removed implies empty; a non-empty value must be a normalised substring of the frozen candidate field |
| edit list length | may only grow; existing positions are corrected in place, never deleted or reordered |
| failure, notes, sufficiency evidence | byte-identical |
| task id set, writer id, schema version | byte-identical |

## Still forbidden

Any character of any candidate field; semantic rewriting of failure, notes or sufficiency evidence;
adding or removing a task; task replacement; re-opening a task for new specification design; and
modifying the writer validator.

## Acceptance order

```
resubmission_identity_gate_v2.py  →  validate_writer_output.py  →  freeze accepted submission SHA256
```

## Sufficiency of the remedy

Applying only A4.1 and A4.2 to a synthetic correction takes the validator from 54 hard failures to 7.
The residue is an artefact of the fixture's crude quotation-completion heuristic, not a third defect
class: correct verbatim completions exist for every remaining entry, verified by hand on W39, where
the quotation differed only in quote characters, and on W54, where two clauses had been merged under
one ellipsis and need one declaration each.
