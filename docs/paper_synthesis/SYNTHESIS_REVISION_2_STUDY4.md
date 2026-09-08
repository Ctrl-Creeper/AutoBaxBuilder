# Paper synthesis revision 2 — Study-4 behavioural line integration

**Document type:** revision provenance for a non-preregistration synthesis gate. This is a
synthesis-provenance record, not a preregistration.
**Revision-1 freeze:** commit `1dda9cf5b3abdca8930900fdc8ac0d92234bb3b8`.
**Trigger:** acceptance of the Study-4C-EX execution and closure of the behavioural experiment line,
2026-09-08.

## What this revision may and may not do

It integrates two already frozen behavioural closures into the four synthesis documents. It reads
only aggregate values that were frozen before this revision began.

- **No frozen raw or results artifact of Studies 1, 2, 3, 4-fresh, 4B, or 4C was rewritten.** The
  one interpretation-wording narrowing accepted at review is recorded as a separate binding
  amendment, `docs/preregistration/2026-09-08_study4c_execution/STUDY4C_WORDING_AMENDMENT_1.md`,
  SHA-256 `dc58cb1e4c6bda264b050431d0029b84a22b1ab9a7e05af2f7cf5fe4ffde0824`, indexed by
  `SHA256SUMS_STUDY4C_AMENDMENT_1`. It changes no number, gate, verdict, or hash, and
  `STUDY4C_RESULTS.md` remains byte-exact at
  `3a5f130d7dceab2e36b6f0c5ef1d7d98174132621144bc9f6bb721ee8e3c8b04`, as does the frozen
  `SHA256SUMS_STUDY4C` index.
- **No Studies 1-3 confirmatory claim was changed.** Claim rows C1-C5, C7, C8, and C10-C12 are
  byte-identical to revision 1; this is checked mechanically.
- No new estimand, coding pass, task-level analysis, subgroup, taxonomy, or outcome was created.
  Study 3's 53 confirmatory tasks and Study 4C's 752 completions remain closed.

## Revision-1 document hashes (superseded content, recoverable at the revision-1 commit)

| Document | Revision-1 SHA-256 |
|---|---|
| `paper_claim_evidence_matrix.md` | `e113a00d12d6efef36e38970c3f329b994d795dab4a369f7cb94ca1d20f511f1` |
| `paper_architecture_v1.md` | `65594f56bf6e69e01242d78ae2a37e7cfabe033da5d664086a6e2767bcf43762` |
| `reviewer_attack_audit.md` | `99f72545a3e7c4c06fe9d9d28f9fac497fc3fad3e854e65d0a9f206fa4f0f75e` |
| `study4_decision_memo.md` | `ae8e9bb5455d4ae56b931b778a656a5c0c1b88a4a68863932bfb3cbc8f7fe25b` |

The three revision-1 consistency reports (`CROSS_DOCUMENT_CONSISTENCY_REPORT.json`,
`..._FINAL.json`, `..._FINAL_V2.json`) and `cross_document_consistency_check.py` are preserved
unchanged. That checker is one-shot and its report exists, so revision 2 adds a separate
`cross_document_consistency_check_v2.py` writing
`CROSS_DOCUMENT_CONSISTENCY_REPORT_STUDY4.json` rather than re-running or editing the frozen one.

## Changes by document

| Document | Change |
|---|---|
| `paper_claim_evidence_matrix.md` | Added frozen-evidence sections for Study 4B and Study 4C-EX. Restated C6 and C9 (C9 remains unsupported as a causal claim). Added C13 (selected-subset behavioural sensitivity), C14 (mechanism not isolated), C15 (fresh Study 4 closed NO-GO), C16 (construct distinction). Added source-register entries S4B-C, S4C-R, S4F. Extended the synthesis ruling. |
| `paper_architecture_v1.md` | New section 6, "Behavioural follow-up on a selected subset" (6.1 fresh-study NO-GO, 6.2 Study 4B, 6.3 Study 4C-EX, 6.4 preserved construct distinction, 6.5 behavioural-line limitations). Old section 6 renumbered to 7. New section 8, the abstract/conclusion claim-wording draft. Claim-boundary paragraph extended. |
| `reviewer_attack_audit.md` | Objection 7 restated as attempted-and-unresolved. New objections 11-14: Study-3 invalidation, `S'` as a different functional specification, the inconclusive mechanism experiment, and generic prompt sensitivity. Residual-risk ordering updated. |
| `study4_decision_memo.md` | Ex ante analysis preserved unchanged with an explicit reading-order note. New final section, "Post-decision record", recording the three executed pieces, what C9 did and did not gain, the CLOSED line status, and that Version A stands. |

## Binding claim boundary for the behavioural line

**Strongest allowed wording — Study 4B** (both sentences, always together, in this order):

> On the frozen 47 demonstrated-separable tasks, model behavior was strongly sensitive to the S
> versus S' specification condition: the determining S condition substantially increased SecurityPass
> while substantially reducing CapabilityPass.
>
> Because CapabilityPass also changed substantially, the SecurityPass contrast cannot be interpreted
> as the isolated causal effect of safety-determining information while functional performance is
> held constant.

**Strongest allowed wording — Study 4C-EX:**

> A matched-control follow-up did not isolate the mechanism underlying the capability shift. Explicit
> interface-contract reinforcement produced no capability recovery relative to a length- and
> structure-matched placebo, while both added-instruction conditions reduced SecurityPass relative
> to S.
>
> The placebo demonstrates that a substantial nonspecific added-instruction effect was present.

**Narrowed consequence statement, binding:**

> The matched placebo demonstrates a substantial nonspecific added-instruction effect on
> SecurityPass, so the S_controlled security loss cannot be interpreted as wholly
> contract-content-specific.

**Preserved distinction, binding:**

> Study-3 capability-determination preservation is a specification-level construct; Study-4B
> CapabilityPass is a model-performance outcome. A change in the latter does not imply the former was
> validated incorrectly.

**Prohibited overclaims.** Each line below is a form of words that must not be asserted anywhere in
the paper or its synthesis artifacts.

| # | Never assert | Why it is prohibited |
|---:|---|---|
| 1 | Never assert that Study 4C proves an intrinsic safety/function conflict. | The H1 read-out required security preservation; the manipulation-integrity criterion failed, so no such conclusion is licensed. |
| 2 | Never assert that Study 4C proves implementation collateral damage. | `Delta_C,mech = -0.0053` `[-0.0939, +0.0833]`: contract reinforcement recovered no capability. |
| 3 | Never assert that `S'` changes the functional specification itself. | Study 3 fixed `S'` under a frozen constraint set with every capability case determined; the behavioural co-movement is a separate, bundled-manipulation limitation. |
| 4 | Never assert that determination causes +50.5 pp security inflation, or state any score-inflation magnitude. | The capability guardrail failed, so the contrast does not identify a causal effect on scores. |
| 5 | Never assert that the security loss was mostly, largely, or entirely generic, and never state any share, fraction, percentage, or ratio attributed to the nonspecific component. | The ratio of `Delta_S,generic` to `Delta_S,preserve` is not an estimand of the design, has no interval, and is protected by no pre-specified criterion. |
| 6 | Never assert that Study 4C invalidates Study 3. | Different construct and different instrument; see the preserved distinction above. |
| 7 | Never assert that the Study-4B capability failure invalidates specification-level separability. | Specification-level determination and model pass behaviour are measured on different objects. |

Additionally carried forward from the frozen closures: capability was **not** behaviorally held
constant; removing safety information alone was **not** shown to cause the effect; the effect does
**not** generalize to SeCodePLT; Study 4B does **not** rescue or replace the fresh Study 4; and
Study 4C is **not** outcome-naive independent confirmation.

## Line status

The behavioural experiment line is **CLOSED**: no Study 4D, no revision of the `S_controlled` or
`S_placebo` blocks, no added repeats, no task-level or subgroup failure mining, no new mechanism
taxonomy, and no post-hoc hypothesis search over the frozen 752 Study-4C completions. The
fresh-sample Study 4 remains separately closed at `0/160` validated pairs, NO-GO.
