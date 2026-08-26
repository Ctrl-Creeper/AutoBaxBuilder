# Round-2 interpretation memo — checkpoint before any further step

**Status.** Frozen interpretive record. Nothing here adjudicates a disagreement, amends protocol v2
(`4ca61b25…`), designs a v3, or executes any new study. It fixes what Round 2 did and did not
validate, so that later documents cannot quietly claim more.

**Inputs** (all previously frozen): `results_pre_adjudication.json` `17300bb1…`,
`diagnostic_disagreement_analysis.json` `f455a9ef…`, both coder submissions (`35916e1c…`,
`1f254579…`), the accepted writer submission `86e2ef6b…`, protocol v2. One new mechanical count is
introduced in §3 and cross-tabulated in §4; it reads frozen artifacts only.

---

## 1. What Round 2 validated, judgement by judgement

### J1 / Determination — prospective blinded reliability evidence, the real result

Two independent blinded coding runs, on 442 cases across 90 tasks selected and frozen before any
specification was authored, applying frozen Definition D to specifications they had never seen:

- raw agreement 0.937; **cluster-aware κ 0.804, 95% CI [0.708, 0.893]** (primary, per frozen C9);
  pooled κ 0.869 (descriptive only, per C8); AC1 0.877 [0.808, 0.936] (sensitivity, not read against
  κ verbal scales, per C9).

This is the one claim Round 2 earns: **the measurement primitive — case-level determination under
Definition D — is reproducible across independent blinded runs, prospectively.** The qualifier from
C5 stands: these are independent blinded coding *runs*, not independent human coders, and correlated
error cannot be excluded.

### J2 / Witness Compliance — variation exists; describable; not the current core

Marginals 40/90 and 39/90 `contradicts_S`; 7 disagreements. J2 varied, so its agreement is
informative in a way J3's is not. No claim beyond that is made here, and none is needed for the
checkpoint.

### J3 / Constructibility — no discriminative support this round

**Both runs answered `exists = true` on all 90 tasks.** A constant cannot disagree, so J3's zero
disagreement is **not** evidence of reliability, and no reliability statement about J3 may cite
Round 2. Round 2 provides *no discriminative support* for the constructibility judgement: the
question was asked 180 times and never once exercised its false branch.

### Consequence

**Round 2 validated the measurement primitive, not the taxonomy.** Every downstream construct that
consumes only J1 (functional sufficiency profiles, oracle underdetermination, per-case determination
rates) inherits the reliability evidence. Every construct that consumes J3 — including the derived
five-class table — does not.

## 2. Correction to the derived-classification reading

The frozen C3 table routes to `STRUCTURALLY_CARRIED` and `INSEPARABLE` only through `J3 = false`.
With J3 constant `true`, both classes were **mechanically unreachable in both runs**.

Therefore, and correcting any earlier text that could be read otherwise:

> **`STRUCTURALLY_CARRIED = 0` and `INSEPARABLE = 0` are not prevalence results.** They are a
> property of the routing under a degenerate input, not a measurement of the corpus. No document may
> cite these zeros as evidence that the classes are rare, and the derived-class marginals
> (SEPARABLE 43/45, NOT_YET_BLINDED 27/21, OVER_STRIPPED 20/24) are marginals of a **three-class**
> instrument as actually exercised, not of the five-class taxonomy.

The derived-class agreement figure (78/90 = 86.7%) likewise describes agreement over the reachable
three classes only.

## 3. J3's constancy is a coder-channel fact, not a study-wide fact

One count, mechanical, from the frozen accepted writer submission: the writer's §4 failure channel —
which the coders were correctly never shown — recorded

| writer declaration | tasks |
|---|---|
| no failure | 53 |
| `F1_LIST_COUPLING` | 25 |
| `F3_PREAMBLE_CARRIER` | 12 |

Constructibility judgements were made **twice** in this pipeline: once by the writer role (with
variation, 53/25/12) and once by the coder role (constant). The study as a whole did not lack
variation in constructibility opinion; **the coder channel did.** The writer's declarations are not
validated measurements and are not treated as ground truth — but their existence rules out the
lazy reading that the corpus simply contains nothing for J3 to detect.

## 4. The reachable classes absorbed the signal

Cross-tabulating writer declarations against both runs' derived classes (mechanical join of frozen
artifacts):

| writer declaration | both runs SEPARABLE | pushed to NOT_YET_BLINDED / OVER_STRIPPED (either run) |
|---|---|---|
| no failure (53) | 37 | 16 |
| F1 / F3 (37) | 5 | 32 |

Where the writer hit an obstruction, the coders' J1 almost always registered it — as safety cases
still determined (→ NOT_YET_BLINDED) or capability cases lost (→ OVER_STRIPPED). The information
"this task resists blinding" **is present in Round 2's data**, carried by J1. What the constant J3
did is route it into classes whose names attribute the resistance to *writer performance*
("not yet", "over-") rather than to the *task* ("structurally carried", "inseparable"). Which
attribution is correct is precisely what a working constructibility measurement would decide, and is
not decided here.

## 5. Dispositions, fixed by this memo

1. **The 28 J1 and 7 J2 disagreements are held as pre-adjudication evidence.** No adjudication.
   Adjudication is not on the critical path: it cannot supply the discriminative support J3 lacks,
   and the J1 reliability result does not need it.
2. **The 90 Round-2 tasks are spent as a prospective validation sample for any revised
   constructibility measurement.** They have been used to expose J3's degeneracy; any future J3′
   designed with that knowledge would meet them as a development set, not a test set. They remain
   valid as what they already are — the prospective sample for the J1 result — and may serve as
   **development evidence only** for constructibility work. This restriction is permanent, in the
   same sense as `INSTRUMENT_DEVELOPMENT_ROUND_1.md`.
3. **Protocol v2 is not amended and no v3 is designed** until the conceptual question — whether J3
   as formulated belongs to a different class of measurement problem — is settled. That analysis is
   `2026-08-26_j3_conceptual_design_analysis.md`, a companion to this memo; it proposes options and
   executes none.
4. Any future citation of Round 2 must carry §1's split: primitive validated, taxonomy not.
