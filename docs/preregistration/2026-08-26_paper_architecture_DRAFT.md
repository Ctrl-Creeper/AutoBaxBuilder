# Paper-level study architecture — Option 2 as a complete paper (DRAFT)

**Status.** Architecture draft for a decision, not a preregistration. Nothing here designs a
protocol, draws a sample, adjudicates a disagreement, or calls an API. The original five-class
taxonomy is **demoted throughout**: the paper is built from the epistemic outcomes the frozen
evidence actually supports, and any final taxonomy is decided after, not before, the studies exist.
Companion to `2026-08-26_round2_interpretation_memo.md` (`8aef7785…`) and
`2026-08-26_j3_conceptual_design_analysis.md` (`fa9fe398…`).

---

## 0. Central claim and research questions

**Central claim.** In leading code-security benchmarks, the oracle's security-relevant behaviour is
frequently *determined by the specification shown to the model* — the test's answer is carried by
the question. This conflates specification-following with security capability. We (i) define this
property precisely as a decidable, quotation-refutable predicate (Definition D), (ii) validate a
measurement instrument for it with prospective blinded reliability evidence, and (iii) show that
the determining information is *demonstrably removable* for a large fraction of tasks and
*verifiably obstructed* for an identifiable fraction — delivering the blinded specifications
themselves as artifacts.

The claim is deliberately **measurement-theoretic, not causal**. A causal extension (Study 4) is
architecturally separated so the paper's completeness does not depend on it (§5).

**RQ1 — Prevalence.** To what extent do security-benchmark oracle behaviours follow from the
specification itself, per Definition D? *(Study 1)*

**RQ2 — Measurability.** Can determination be measured reliably by independent blinded runs?
*(Study 2)*

**RQ3 — Separability.** Where the specification determines the security oracle, to what extent can
that information be removed while preserving functional adequacy — *demonstrably*, with the evidence
graded as demonstrated / verifiably obstructed / unresolved? *(Study 3)*

**RQ4 — Consequence (extension).** Does the presence of oracle-determining information causally
change measured model security performance? *(Study 4)*

---

## 1. Study 1 — Benchmark characterization / Determination prevalence

**RQ.** RQ1: what fraction of ⟨specification, oracle behaviour⟩ pairs in the original, as-shipped
benchmarks are determined, and how does determination distribute over capability vs safety cases
and over carriers (prose / signature / setup)?

**Benchmarks and their evidential grade.**

| benchmark | role | grade |
|---|---|---|
| SeCodePLT | formal prevalence measurement — the instrument is built for its harness structure (setup + code_before/after, capability/safety testcases) | **formal, new data required** |
| CWEval | structural characterization: 62/119 tasks with no security-specific assertion | exploratory (already frozen) |
| PurpleLlama | structural characterization: no functional tests; linter as oracle — Definition D-style coding is inapplicable as-is | exploratory (already frozen) |
| our own generator (AutoBaxBuilder) | motivation / origin: 35% functional-test entanglement, 89–91% spec-grounding | exploratory (already frozen) |
| SeCodePLT's own ablation | evidence that the field's existing mitigation is incomplete: the `security_policy` switch blinds only ~14% of tasks; the obligation survives in the non-gated `raise` field | exploratory (already frozen) |

**Measurement unit.** The **case** — one ⟨specification, oracle behaviour at input *i*⟩ pair — with
**task-clustered inference** (the Round-2 machinery: cluster-aware statistics, task-level bootstrap).
Task-level summaries are *derived* quantities and are reported as such: the Round-2 diagnostic
showed three tasks flipping their derived class on a single case judgement, so the case is the
stable unit and any task-level figure inherits that brittleness explicitly.

**What is exploratory vs what must be formally measured.** Everything currently frozen about
*original* specifications is exploratory: the cross-benchmark structural findings above, IDR1's
rates (18/23, 0/24 — development round), and the 10–12-task feasibility study. **The formal gap is
precise: Round 2 coded the writer's candidates S′, never the original specifications.** So the
paper's headline prevalence number — determination in the benchmark as shipped — does not yet exist
at formal grade. It requires two new independent blinded J1 runs over original specifications.
Whether those runs may target the existing 90 tasks (a frozen random sample whose *original* specs
no coding run has seen) or must use a fresh slice is an open design decision, flagged here and not
taken: the 90 are burnt for constructibility-instrument validation (memo §5.2), and the argument
that J1-prevalence coding of their originals is uncontaminated must be made — or refused — in a
frozen protocol, not in this draft.

---

## 2. Study 2 — Measurement validation

**Placement.** Round 2 — 90 tasks, 442 cases, prospectively frozen sample, blinded independent runs,
preregistered analysis — is the paper's psychometric core, presented **as validation of the
measurement primitive J1/Determination and of nothing more**. The paper states in the main text, not
the appendix, that the constructibility judgement (J3) returned constant assent and therefore
received no discriminative support, and that this is what motivates Study 3's redesign of
constructibility as a procedure. The failure is part of the contribution: it is the evidence that
existence claims cannot be annotated (analysis doc, Part I).

**Main-text numbers.**

- raw agreement 0.937; **cluster-aware κ 0.804, 95% CI [0.708, 0.893]** (primary, per frozen C9);
- the design facts that give the number its force: sample frozen before authoring, coders blinded,
  analysis code committed before execution, per-case unit with task-clustered bootstrap;
- the C5 qualifier, verbatim in the main text: independent blinded coding **runs**, not independent
  human coders; correlated error not excluded; human replication is a higher validation grade left
  open.

**Appendix / limitations.**

- pooled κ 0.869 (descriptive only, upward-biased under clustering — with the demonstration);
- AC1 0.877 [0.808, 0.936] as skewed-marginal sensitivity, fenced from κ verbal scales;
- ICC (0.412 / 0.360), tie-break rates (18.8% / 24.0%) and the tie-break-direction caveat;
- J2 description (40/90, 39/90, 7 disagreements) — reported, not load-bearing;
- quote concordance (0.703 exact / 0.919 same-passage) and the five non-locatable quotes as an
  instrument gap;
- the derived-class table **only with the memo §2 correction attached**: three reachable classes,
  zeros not prevalence;
- the 28 + 7 disagreements as pre-adjudication evidence, unadjudicated.

Nothing from Round 2 enters the paper as evidence about the taxonomy.

---

## 3. Study 3 — Constructive separability

**Reframing.** Constructibility is not an annotation; it is an **evidence-producing procedure** with
three epistemic outcomes per task:

| outcome | what earns it | what it licenses |
|---|---|---|
| **demonstrated-separable** | a produced candidate S′ passes the J1-based check: blinded runs find all capability cases determined, no safety case determined | an existence claim, carried by an inspectable artifact — the blinded specification itself |
| **verified-obstruction** | the construction attempt terminates in a structured, quotable obstruction record (coupling or structural carrier), independently verified the way J1 quotes are verified | a nonexistence claim *relative to the stated constraints*, carried by a checkable argument |
| **unresolved** | neither: construction failed but no verifiable obstruction was produced | nothing — explicitly |

**Why failure-to-construct is not inseparability.** A failed attempt is evidence about the
*procedure* — the writer's skill, budget, and search — not about the space of all specifications.
"No witness found" and "no witness exists" differ by an unbounded quantifier; collapsing them is
exactly the category error that made J3 constant, run in the opposite direction. Round 2 makes this
concrete: the writer's 37 failure declarations coexist with coder evidence that 5 of those 37
candidates in fact achieved separation — the writer's own failure channel has a measured false-
positive direction. An unverified failure therefore lands in **unresolved**, and inseparability is
never inferred from absence; it must be *argued*, quotably, and survive independent verification.

**Estimand.** Partial identification: the demonstrated-separable rate is a **lower bound** on
separability; the verified-obstruction rate is a **lower bound** on inseparability; the unresolved
band is the honest gap between them. No population-level binary constructibility label is claimed
(see §7 for why the paper is complete anyway).

**Existing evidence.** Round 2 is this procedure's *pilot, run unknowingly*: candidates exist for 90
tasks; blinded J1 over those candidates exists; the writer's F1/F3 declarations are proto-obstruction
records; the memo §4 cross-tab (37/53 no-failure → both-runs-separable-profile; 32/37 declared-
failure → blocked profile) is the pilot's result. All of it is **development evidence** — the 90 are
spent (memo §5.2) — so the formal study requires a fresh sample, a frozen procedure, and independent
obstruction verification. Not designed here.

---

## 4. Study 4 — Controlled manipulation / causal validation

**Hypothesis.** For demonstrated-separable tasks, model *security* pass rates drop when the
oracle-determining information is removed from the specification, while *capability* pass rates are
preserved — i.e., some measured "security capability" is specification-following. The manipulation
is the paper's earlier 2×2: oracle-determining information present/absent × security framing
present/absent, on the same tasks, same harness, same model.

**What it actually tests.** RQ4 — the *consequence* claim. Studies 1–3 establish that the leakage
exists, is measurable, and is removable; Study 4 tests whether models **use** it. Without Study 4
the paper claims a validity threat; with it, a demonstrated inflation.

**Necessary or enhancement?** **Enhancement — by architectural choice.** The central claim (§0) is
measurement-theoretic, so the paper is complete without Study 4; the strongest reviewer attack that
remains is "no evidence models exploit the determination" (§8), which the paper must then answer by
positioning: benchmark validity does not require proof of exploitation, any more than test-security
requires proof that students read the leaked answer key — the leak itself is the defect, and the
blinded artifacts are the fix. That said, Study 4 is the highest-leverage addition per unit cost:
Study 3's demonstrated-separable artifacts are literally its stimulus set, the harness
(`secodeplt_task_runner.py`) is built and self-checked, and it is the only study requiring eval API
spend. Decision rule proposed: **publish-without if Study 3's demonstrated-separable count is small;
run Study 4 if it is large enough to power the comparison** — the exact threshold belongs to a
frozen protocol, not this draft.

---

## 5. Claim–evidence matrix

| claim | study | evidence now | new data needed |
|---|---|---|---|
| A. Oracle-determination leakage is structural and industry-wide | 1 (exploratory tier) | frozen: CWEval 62/119, SeCodePLT shared-assertion + ablation gap, PurpleLlama structure, own-generator origin | none (reported as exploratory characterization) |
| B. Determination is precisely definable and reliably measurable | 2 | **frozen, formal: Round 2** (κ 0.804 [0.708, 0.893], prospective, blinded, preregistered) | none |
| C. Determination prevalence in the benchmark as shipped | 1 (formal tier) | none at formal grade (Round 2 coded S′, not originals) | **two blinded J1 runs on original specs** (no API) |
| D. Separability is demonstrable for a bounded-below fraction; obstruction verifiable for another | 3 | pilot-grade only: Round-2 candidates + J1 profiles + writer F1/F3 channel + memo §4 cross-tab | **one frozen procedure run on a fresh sample** (writer + two J1 runs + obstruction verification; no eval API) |
| E. Annotation cannot measure existence claims; procedures can | 2→3 bridge | frozen: J3 constancy + conceptual analysis Part I (text-decidable defects) | none |
| F. Models exploit determination (score inflation) | 4 | none | eval runs (API) — the only API-spending study |

**Minimal publishable version.** Studies 1 + 2 + 3 → claims A–E. New data: item C's coding runs and
item D's procedure run — conversation cost only, zero eval API. Central claim fully supported.

**Full version.** Add Study 4 → claim F, upgrading the paper from validity-threat to demonstrated
inflation, at the cost of API spend and one more preregistration cycle.

---

## 6. Biggest reviewer attack surfaces, ranked

1. **"Runs, not humans."** All reliability evidence comes from independent blinded LLM coding runs
   sharing a model lineage; correlated error is not excluded. Held everywhere the C5 qualifier
   appears; a small human replication remains the single best hardening if ever affordable.
2. **"So what?" (absent Study 4).** No demonstration that models exploit the leak. Answered by the
   test-security positioning in §4, or dissolved by running Study 4.
3. **Procedure-relative bounds.** "Your demonstrated-separable rate measures your writer."
   Conceded by construction — it is a lower bound and says so; a second independent writer widens it.
4. **Single-benchmark formality.** Formal measurement is SeCodePLT-only; CWEval/PurpleLlama enter as
   structural characterization. The defense is explicit scoping, not overclaiming.
5. **A wide unresolved band.** If Study 3's middle is large, the bounds risk vacuity. Mitigations
   are reporting-side (the band is itself a finding about the procedure's cost) — but this is the
   main empirical risk to the paper's punch.
6. **Definition D's counterfactual reader.** "A competent implementer obliged by S" invites
   subjectivity charges; answered by the quotation requirement and the Round-2 agreement itself.
7. **The retired taxonomy.** Reviewers who saw earlier framings may ask where STRUCTURALLY_CARRIED /
   INSEPARABLE went. The answer is §7's grading: labels are not asserted beyond the epistemic
   outcomes that earn them.

---

## 7. The completeness question

**Question.** If Study 3 delivers only a demonstrated-separable lower bound, a verified-obstruction
lower bound, and an unresolved middle — no population-level binary constructibility label — is the
paper still complete?

**Answer: yes, and it is *more* complete than the binary alternative, for four reasons.**

1. **A paper is complete when every claim is matched by evidence of the stated grade and every RQ is
   answered at the grade it was posed.** RQ3 is posed as "to what extent is separability
   demonstrable" — a partial-identification question. Bounds answer it exactly. The version of RQ3
   that a binary label would answer ("what fraction of tasks *are* separable, simpliciter") is
   precisely the question the conceptual analysis proved unanswerable by annotation — J3's constant
   is the frozen empirical record of what happens when it is asked anyway. Completeness is measured
   against answerable questions.

2. **The binary label is strictly dominated.** Bounds + unresolved band carry *all* the information
   a binary labelling would, plus an honest account of the gap: any consumer who insists on a binary
   reading can impose one on the band and sees exactly how much of the conclusion is assumption. The
   binary label is the same object with the assumption hidden. Partial identification is a mature
   estimand class (interval-valued conclusions are standard in econometrics and in program
   verification's verified/falsified/unknown), not a concession.

3. **The paper's deliverables never needed the label.** For benchmark consumers, the actionable
   output is the set of demonstrated-separable tasks *with their blinded specifications attached* —
   an artifact, usable regardless of any population claim. For benchmark builders, the actionable
   output is the verified obstruction records — quotable design constraints (coupling, preamble
   carriers) that explain *why* certain tasks resist blinding and what harness changes would relieve
   them. Both deliverables are per-item and evidence-carrying; a population binary adds rhetoric,
   not use.

4. **The unresolved band is a finding, not a residue.** Its size measures the cost of honest
   constructibility assessment under stated constraints — the first quantification of that cost in
   this literature, and the direct successor to the observation that SeCodePLT's own one-line
   ablation silently mislabels the band as "handled".

What *would* make the paper incomplete: a central claim that quantifies inseparability as a
population property, or any revival of the five-class taxonomy as an asserted partition. Both are
excluded by construction — the taxonomy stays demoted until the epistemic outcomes exist, and if a
final taxonomy is ever reinstated, its classes must coincide with outcome grades actually earned
(demonstrated / verified / unresolved), not with the annotation-era labels.
