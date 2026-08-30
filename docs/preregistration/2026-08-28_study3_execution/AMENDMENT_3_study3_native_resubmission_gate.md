# Amendment 3 (2026-08-29) — Study-3-native writer resubmission gate

**Nature.** Execution-instrument compatibility amendment, ruled by the PI after the
pre-build mechanical check ordered with the writer-handoff approval found the Round-2
frozen resubmission gate incompatible with the frozen Study-3 writer schema — **before any
writer package was built and before any writer output exists**. It changes no part of
constraint set C, the DS/VO/UR definitions, eligibility, the estimand, or the writer's
substantive task. The frozen protocol (`548addbd…`) is not rewritten; Interpretation
Note 1's ruling 5 hard-stop worked as designed and this amendment records its outcome.

## GAP-4 (discovery record) — Round-2 gate mechanically incompatible with Study-3 schema

Found statically, with zero writer outcome observed:

1. The Round-2 gate's byte-freeze invariant (`spec_hash`) covers exactly five prose
   fields; the Study-3 candidate has a sixth substantive field, `security_policy`
   (editable/removable — the central manipulated component), whose value changes would
   pass the Round-2 gate silently.
2. The v2/v3 flagged-set machinery parses the Round-2 validator's human-readable failure
   strings from a report keyed `hard_failures`; the frozen Study-3 candidate validator
   emits differently-worded `problems` — the machinery cannot load a Study-3 report.
3. `ANCHOR/PREV/REPORT/TASKS` paths are hardcoded into the Round-2 handoff directory;
   "exactly as frozen" would compare a Study-3 resubmission against Round-2 artifacts.

**Resolution (PI ruling, path b):** no longer claim "exactly reuse the Round-2 gate
implementation". Instead: **reuse the frozen Round-2 resubmission discipline, implemented
prospectively against the frozen Study-3 schema.**

## Binding clauses (ruling verbatim in substance)

1. **First submission is the only substantive anchor.** The writer's first complete
   submission, the moment it is received: raw bytes saved, SHA256 recorded, marked
   `FIRST_SUBMISSION_ANCHOR`, permanently retained before any repair/resubmission. The
   gate never alters the anchor (`resubmission_gate_study3.py --anchor`, refuses
   overwrite).
2. **All six candidate fields are substantively frozen** —
   description/context/arguments/return/raise/**security_policy** — under a canonical
   serialization with a per-task candidate hash. `security_policy = null` and a string
   are different values; null↔string conversion is a substantive change and is forbidden
   in a resubmission. A redundant **whole-task substantive-object hash** (candidate +
   obstruction declaration + evidence + notes + edit substance) and a whole-submission
   hash are enforced in addition to field-level checks.
3. **The allowlist is frozen now, once.** No A4 interface and no "new repair class after a
   validator failure" ever. Frozen classes:
   - **A1 serialization/container repair** — UTF-8 BOM, markdown code fences, stray bytes
     outside the outermost JSON object, dict-key casing, a bare `edits` object promoted to
     a one-entry list. Never changes any parsed substantive value.
   - **A2 required-metadata completion/normalization** — `schema_version` set to the fixed
     constant `study3-writer-v1`; `writer_id` filled **only if empty** (a non-empty
     writer_id is frozen). Nothing else is metadata.
   - **A3 mechanical provenance/traceability repair** — `edits[]` container/key-shape
     repair with **all five parsed values unchanged** (field compared lowercased,
     original, action, replacement, why). Round-2's provenance-append allowance is NOT
     carried over: the Study-3 validator demands no provenance completeness, so no flag
     can ever license an append; `edits[]` length and order are frozen.
   If a validator failure cannot be resolved by A1–A3 alone, the first submission stands
   as the formal writer output and the resubmission pathway for that submission ends.
4. **Obstruction declarations are anchored against outcome-driven mutation.** The
   substantive anchor includes: the obstruction class (`failure` null vs object and its
   `code`), `at_case`, `detail`, the quoted evidence (`quotes[]`), `sufficiency_evidence`,
   and `notes`. A resubmission may not turn `none` into an F-code or back, change a quote,
   add an obstruction, or change the writer's declared success/failure — the substantive
   hashes make any such change a hard reject, protecting the future VO pathway from
   post-validation repair contamination.
5. **Structured interface, no regex on prose.** The frozen candidate validator now emits
   machine-readable issue codes (format extension only; no substantive check weakened,
   none removed; done now because zero writer outcome exists). Frozen enumeration and
   licensing map — codes not listed as repairable admit no repair:

   | issue code | licenses | meaning |
   |---|---|---|
   | `INVALID_SERIALIZATION` | A1 | submission bytes not a parseable JSON object |
   | `TASK_SHAPE_ERROR` | A1 (casing only) | task-level key set wrong |
   | `CANDIDATE_SCHEMA_ERROR` | A1 (casing only) | spec key set wrong / spec not an object |
   | `OBSTRUCTION_SHAPE_ERROR` | A1 (casing only) | failure object key set/type wrong |
   | `MISSING_REQUIRED_METADATA` | A2 | schema_version wrong/missing; writer_id empty |
   | `PROVENANCE_SHAPE_ERROR` | A3 | edits not a list / entry key set wrong |
   | `TASK_SET_ERROR` | — unrepairable | task missing/added/renamed; tasks not an object |
   | `EMPTY_CANDIDATE_FIELD` | — unrepairable | a prose field empty (candidate must ship) |
   | `SECURITY_POLICY_INVALID` | — unrepairable | empty string / wrong type (""≠null is an interpretation, not a repair) |
   | `IMMUTABLE_COMPONENT_CHANGED` | — unrepairable | a parameter no longer mentioned (constraint C) |
   | `PROVENANCE_VALUE_INVALID` | — unrepairable | edits action outside removed/rewritten |
   | `OBSTRUCTION_CODE_INVALID` | — unrepairable | failure code outside F1–F5 |
   | `OBSTRUCTION_EVIDENCE_MISSING` | — unrepairable | failure without quotes |
   | `QUOTE_NOT_LOCATABLE` | — unrepairable | failure quote absent from the task file (quotes are frozen evidence) |
   | `NOTES_TYPE_ERROR` | — unrepairable | notes not a string |

   "Licenses A1 (casing only)" means: the code admits entry to the gate, but acceptance
   still requires every substantive hash unchanged — a missing key, an added key, or any
   value change under these codes fails the substantive invariant and is rejected.
6. **Three outcomes, per task and per submission:** `ACCEPT_FIRST` (no validator flag —
   nothing may be resubmitted), `ACCEPT_REPAIRED` (only flag-licensed non-substantive
   repair occurred; every substantive anchor hash identical; the frozen candidate
   validator must then also pass, in that order, before any freeze), and
   `UNREPAIRABLE_FIRST_SUBMISSION` (≥1 flag outside the licensing map). The third never
   deletes a task and never auto-classifies anything as VO.
7. **Adversarial fixtures** (`test_resubmission_gate_study3.py`) prove every clause-7
   item listed in the ruling, including the substantive-hash identity of every accepted
   repair.
8. **Data-flow.** The gate reads exactly: the first-submission anchor bytes, the candidate
   validator's machine report (bound to the anchor by `submission_sha256`), and the
   resubmission. The coder-side §3 artifacts, the measured-membership manifest and its
   per-task case indices, Study-1/Round-2 outcomes, future S′ verifier results, and
   DS/VO/UR results are unreachable (mechanically audited: dedicated ban list + tight
   import allowlist in `dataflow_audit.py`).
9. **Freeze gate.** Amendment 3 + native gate + validator structured codes + fixtures +
   consistency/data-flow audits all pass → SHA256 + commit → stop. The writer package
   remains unbuilt; no writer session starts under this amendment.

## Schema keys — substantive vs repairable (clause 3 enumeration, exhaustive)

| key | class |
|---|---|
| `schema_version` | repairable metadata (A2: fixed constant; carries no writer content) |
| `writer_id` | repairable metadata, completion-only (A2: empty→non-empty; non-empty value frozen) |
| `tasks` id set | **substantive** — frozen (no add/remove/rename) |
| `tasks.*.spec.description/context/arguments/return/raise` | **substantive** — value-frozen |
| `tasks.*.spec.security_policy` | **substantive** — value-frozen incl. null-vs-string-vs-absent distinction |
| `tasks.*.sufficiency_evidence` | **substantive** — frozen |
| `tasks.*.failure` (null vs object; `code/at_case/detail/quotes` values) | **substantive** — value-frozen; zero value-level repair surface (key casing only, via A1) |
| `tasks.*.notes` | **substantive** — frozen, including type |
| `tasks.*.edits[]` entry values (field lowercased, original, action, replacement, why), length, order | **substantive** — value-frozen |
| JSON container/serialization (BOM, fences, stray outer bytes, whitespace, dict-key casing, bare-edits-object promotion) | repairable (A1/A3, flag-licensed) |

A canonical-serialization comparison level (key lowercasing outside task ids; bare edits
object → one-entry list) makes A1/A3 repairs invisible to the substantive comparison,
exactly as Round-2's gate lowercased `edits[].field`; everything the canonicalization
does not erase is substantive and must hash identical.

## Clause 6 — downstream of UNREPAIRABLE_FIRST_SUBMISSION: what the protocol derives, and GAP-5

**Derivable from the frozen protocol (no new rule made here):** the outcome layer.
Protocol §2 defines Sep via ∃ S′ **satisfying C**; §1 makes DS require a concrete
candidate passing the two-run witness check, writer output alone never DS; §6 derives VO
only from certificates verified against the *original* immutable materials and the §3
runs — never from S′ runs or writer output; §1 makes UR "neither", absorbing every doubt.
Hence, mechanically: a task whose permanent formal writer output is unrepairable-defective
cannot furnish a C-conforming verified witness through that output, so it is never DS via
it; it is never auto-VO; absent an independently valid §6 certificate it lands UR. That is
the protocol's own error-flow default, not a rule introduced by this amendment.

**GAP-5 (OPEN — identified now, before any writer session, per clause 6):** the
*operational* branch is protocol-undefined: whether tasks from an unrepairable first
submission whose individual candidates still pass the per-task mechanical invariants — or
any task from a never-accepted submission — enter the S′ packet build and consume the two
blinded witness runs. The outcome layer is invariant to this choice (a passing profile on
a non-C-conforming or never-accepted candidate is not DS; a failing profile is not VO).
No default is adopted here. **A PI ruling is required before the S′ packet-build stage**;
it affects no writer-visible material, so the writer stage itself is not blocked by GAP-5.

## Disclosure

Amendment 3 was introduced **after** the baseline reveal (m = 53 known) but **before any
writer package, writer session, or writer output existed**. It cannot be conditioned on
writer outcomes (none exist) and touches only the resubmission instrument: selection,
eligibility membership, constraint set C, the writer task, and the DS/VO/UR definitions
are byte-unchanged. The paper must disclose GAP-4, this amendment, and its timing, in the
same manner as Amendment 2.
