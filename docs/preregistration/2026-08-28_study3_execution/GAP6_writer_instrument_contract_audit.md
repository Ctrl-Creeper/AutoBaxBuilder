# GAP-6 — Writer Instrument Contract Audit (static, read-only)

Status: post-Run-1 instrument audit, ruled open by the researcher on 2026-09-07 after the
writer arm reached UNREPAIRABLE_FIRST_SUBMISSION (commit `4d5e4db`). Run-1 artifacts are
untouched. Nothing in this audit reads candidate prose, security_policy content, edit
substance, obstruction rationales, task/CWE identity, baseline judgments, or any outcome.

## Question

Does the writer-visible frozen contract actually state the two validator requirements
whose failure codes terminated Run 1? The standard is literal presence in writer-visible
frozen material — not what a writer could have inferred.

## Audited artifacts (hashes verified against frozen sums before reading)

| artifact | role | sha256 | frozen in |
|---|---|---|---|
| `validate_study3_candidate.py` | validator (requirement source) | `5ea8e4c5e5da7d2cc8445229dac9077e4b41f85aa1b65ec6f05cbbd2e0dd7607` | SHA256SUMS_TOOLING |
| `writer_package/INSTRUCTIONS.md` | writer-visible | `260a925e9ee3972efe7df285aab6445fb9a8bfef84aa1c0a7f45cdb9da51add3` | SHA256SUMS_WRITER_PACKAGE |
| `writer_package/output_template.json` | writer-visible | `9eae55df33045bab2e0cb8fe42aa7a2a492d0a29b3717b7f57a91869ebae6fee` | SHA256SUMS_WRITER_PACKAGE |
| `STARTUP_PROMPT_WRITER.txt` | writer-visible | `75a98cf613a50ae9b591f43c5ecdd21a800b92413f56dcff8d48ef889eaf9cfa` | SHA256SUMS_TOOLING |
| task-file framing (`render_writer_task` on a dummy record) | writer-visible | derived from builder, tooling freeze | SHA256SUMS_TOOLING |
| `validator_report_on_ANCHOR.json` | issue codes/counts only | `8039a41b…` | SHA256SUMS_WRITER_FROZEN |

Run-1 codes confirmed from the report: `PROVENANCE_VALUE_INVALID` ×45,
`EMPTY_CANDIDATE_FIELD` ×37; 82 issues; no other code present. Only these two contracts
are audited (gate scope). Other validator invariants were not audited.

## Q1 — PROVENANCE_VALUE_INVALID

**Validator requirement** (`validate_study3_candidate.py:92-94`): every `edits[]` entry's
`action` must be one of exactly `removed` / `rewritten`; any other value is an issue.

| writer-visible location | what it says | covers the requirement? |
|---|---|---|
| INSTRUCTIONS §4 (lines 66-67) | `edits[]` with `{field, original, action, replacement, why}` per clause removed or materially changed | names the key `action`; **never enumerates admissible values** |
| INSTRUCTIONS §2 table | "editable and removable", "you may instead rewrite it, or keep it" | natural-language description of moves on Security Policy; not tied to the `action` field |
| INSTRUCTIONS §4 | "removal needs no `edits` entry, every other removal does" | speaks to when an entry exists, not to its `action` value |
| `output_template.json` | `edits: []` in all 53 tasks; string `"removed"`/`"rewritten"`/`"action"` absent from the entire file | no example entry, no enum |
| STARTUP_PROMPT_WRITER.txt | no occurrence of `removed`, `rewritten`, `action` | — |
| task-file framing (Reminder) | "Security Policy may be removed entirely" | natural language; not the field vocabulary |

**Verdict Q1: ABSENT.** The admissible `action` vocabulary `{removed, rewritten}` appears
in no writer-visible frozen artifact. The only writer-visible phrase describing the second
category is "materially changed" (§4), which is not the token the validator accepts.

## Q2 — EMPTY_CANDIDATE_FIELD

**Validator requirement** (`validate_study3_candidate.py:68-71`): each of the five prose
fields `description, context, arguments, return, raise` must be a non-empty (non-whitespace)
string in every task, including tasks carrying a `failure` declaration.

| writer-visible location | what it says | covers the requirement? |
|---|---|---|
| INSTRUCTIONS §4 (lines 63-64) | `spec.description` … `spec.raise` (strings, the five prose fields of S′) | type "strings"; **no non-empty requirement**, no per-field "always" |
| INSTRUCTIONS §1 / §3 / Reminder / startup prompt | "Every task gets a candidate", "still ship your best candidate" | task-level obligation; does not state that each of the five fields must be non-empty |
| `output_template.json` | all five prose fields pre-filled with `""` in all 53 tasks; `"empty"` absent from the file | the template's shape *is* the failing state; nothing marks `""` as invalid to submit |
| STARTUP_PROMPT_WRITER.txt | no occurrence of `empty` | — |

The sentence stating this requirement exists only in the validator's own docstring
(line 9-10) and issue message (line 70) — neither is writer-visible.

**Verdict Q2: ABSENT.** The field-level non-empty requirement appears in no
writer-visible frozen artifact; the template presents empty strings as the starting shape
without marking them as unsubmittable.

## Determination

Both audited requirements are ABSENT from the writer-visible frozen contract. Per the
gate's result rule, Run 1 is marked:

**WRITER_INSTRUMENT_CONTRACT_FAILURE**

The mechanical terminal state UNREPAIRABLE_FIRST_SUBMISSION (commit `4d5e4db`, anchor
`2145816f…`, gate verdict `357e241e…`) remains a true, permanently retained execution
result. It is **not** to be read as construct-level evidence that the 53 tasks are
non-separable, and no Study-3 identification region is formed from it at this time.

## Proposed minimal repair (NOT applied; frozen separately as `GAP6_proposed_repair.diff`)

Scope: adds to INSTRUCTIONS §4 exactly the two mechanical requirements already frozen in
the validator and missing from the writer-visible contract — (1) the admissible
`edits[].action` vocabulary, (2) the per-field non-empty requirement. Nothing else changes:
no security/separability strategy, no Definition-D elaboration, no worked examples, no
change to constraints C, validator, gate, scorer, or template. The wording is derived from
the validator source alone, not from any Run-1 candidate content.

Applying it would require a tooling amendment (the text lives in the frozen
`WRITER_INSTRUCTIONS` constant of `build_study3_writer_handoff.py`), a rebuilt package
with new sums, a fresh audit, and a separately approved fresh Writer Run 2. None of that
is authorised by this gate.

## Paper disclosure

Run 1's writer arm terminated on two validator requirements that the frozen writer-facing
contract never stated. The termination is reported as an instrument contract failure; the
Run-1 artifacts are retained unaltered.
