# GAP-2 — the frozen case unit is not mechanically extractable on most of the CWEval frame

**Status.** Tooling implementation halted at discovery, per instruction: no extraction rule was
invented, no packet material was generated, and no builder/validator/scorer was written. Nothing
here uses any SeCodePLT result or any prior CWEval exploratory determination finding.

## The gap

The frozen protocol §3 defines the case unit as "one `pytest.param(inputs…, expected_output)`
entry", and J1 judges whether S_t determines **the expected behaviour b at input i**. That
presumes each param mechanically carries its expected behaviour. On the actual eligible frame it
does not:

| structural class (per file) | files | security cases | functionality cases |
|---|---|---|---|
| **A** — a parametrize name contains `expected`: b is in the param | 16 | 32 (17%) | 49 |
| **B** — params carry `test_type`, no expected name: b lives in test-body branching | 39 | 44 (24%) | 44 |
| **C** — other/mixed parametrize shapes | 59 | 110 (59%) | 155 |
| of which: a params list is built by code, not a literal list | 11 | — | — |

(Full per-file classification: `gap2_structural_classification.json`. Two families are internally
mixed across classes. Additionally, on at least one file — `cwe_022_0_test.py` — the frame's
mark-occurrence count disagrees with the AST param count (3 vs 2 security), so the frozen frame's
case totals themselves carry a counting-method sensitivity that class-A extraction would surface.)

For classes B and C — **83% of the security-case frame** — deriving b at i requires interpreting
test-body logic (what the test asserts when `test_type == …`). No frozen rule defines that
derivation; it is not a presentation transformation but a semantic extraction, and any rule
written now would be authored with knowledge of the frame's structural landscape.

## Exposure ledger

Quantifying this gap used AST structure only: assignment-target names, list literalness,
`parametrize` name strings, and param counts. No param values, no test-body statements, and no
task-file (S_t) content were read. Deeper inspection — e.g. reading param values or test bodies to
design an extraction rule — is itself case-level prior exposure of the kind that excluded
`cwe_943_0`, and is not taken without an explicit decision on admissible exposure.

## What this blocks and what it does not

Blocked: the packet builder's case table, hence all downstream tooling, for classes B/C.
Not blocked: S_t generation (the `BEGIN PROMPT` slice and `DirectPrompt` wrapper are unaffected),
the frame, the census ruling, Definition D, and the Study-1 arm, which is complete and untouched.

## The decision space (reported, not chosen)

1. **Restrict the frame to class A** — mechanically clean, but 16 files / 32 security cases, an
   inclusion-rule change requiring explicit approval and shrinking the arm to near-anecdote.
2. **Freeze a body-interpretation extraction rule** — requires a protocol amendment defining the
   rule and an explicit ruling on how much structural/case-level exposure its design may consume,
   with that exposure disclosed as prior exposure of the coding.
3. **Exec-based materialization** (running the shipped test files to enumerate params) solves only
   the non-literal-list subcase, not expected-behaviour derivation.
4. **Demote the CWEval arm** to structural characterization (its B1 "case-level oracle" cell was
   assessed on `cwe_943_0`-shaped files, which class A resembles; the frame-wide structure is more
   heterogeneous than that assessment suggested).

No option is exercised. Halted pending decision.
