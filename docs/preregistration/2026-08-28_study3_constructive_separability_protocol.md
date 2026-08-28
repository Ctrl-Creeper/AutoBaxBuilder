# Study 3 — Constructive separability: protocol (FROZEN 2026-08-28)

**Status.** Frozen protocol. Integrates the CR-1 ruling (resource-fixed one-stage sampling,
recorded verbatim-in-substance in §9) and the estimand–estimator audit (`c666d69c…`, commit
`9547824`), whose verdicts are binding on §2 and §7. No task outcome is generated, no sample is
drawn, no writer or coder session exists, no API evaluation runs. Study 4 remains closed. No TBD,
no open decision, no adaptive branch, and no interface that permits a rule change after any
outcome is observed.

---

## 0. Design reconciliation — what is already committed, and where

Recovered verbatim-in-substance from frozen documents; nothing below is new:

| commitment | source |
|---|---|
| Study 3 measures constructive separability via an evidence-producing procedure with outcomes DS / VO / UR; annotation of existence claims is retired | architecture draft `e3fcad18…` §3; J3 analysis `fa9fe398…` Part I |
| σ = E[Sep(t)] defined via Definition D and a frozen constraint set **C**, independent of the procedure; identified set **[P(DS), 1−P(VO)]**, sharp under A-DS/A-VO; UR assumption-free; all hesitation flows into UR | PI note `743da509…` §§1–4 — the note's Imbens–Manski inference sketch is **superseded** by the estimand–estimator audit (`c666d69c…`, commit `9547824`): per-endpoint Clopper–Pearson adopted; bootstrap endpoint CIs and IM/combined intervals rejected (§2) |
| A-DS conservative construction: DS only on the agreement of both blinded runs' profiles | PI note §3 |
| Round-2 J3's constant TRUE is **instrument-development evidence only** — the reason measurement moved to witness/proof form; it is never a Study-3 outcome, and the 90 Round-2/Study-1 tasks are development material for constructibility work, permanently | interpretation memo `8aef7785…` §§1,5.2 |
| Writer role: every task ships its best candidate; structured failure declarations (F1–F5 heritage) are recorded, never silently dropped | Round-2 writer INSTRUCTIONS §4 (package `d6948dd1…`) |
| The measured specification boundary: S_t = benchmark default `get_prompt` output — seven labelled fields + setup block + closing instruction; no rendered signature | Study-1 protocol `e4e08330…` §3 |
| RQ3 is posed **conditionally**: "*where the specification determines the security oracle*, to what extent can that information be removed" — the conditional subpopulation predates every Study-1 outcome | architecture draft `e3fcad18…` §0 (RQ3) |
| Contradiction event DS∧VO = instrument-defect halt | PI note §2 |

## 1. Outcome definitions (fixed form)

For each eligible task *t* under constraint set **C** (§4):

- **DS (demonstrated-separable).** A concrete candidate S′ exists and passes the witness check:
  in **both** independent blinded J1 runs over S′, every capability case is determined and no
  safety case is determined. The witness — S′ itself — is the deliverable. **Writer output alone —
  success, confidence, or declared failure — is never DS**: only the frozen two-run J1 criterion
  on a concrete S′ establishes it.
- **VO (verified-obstruction).** A certificate meeting a pre-defined proof standard (§6) is
  independently verified, sufficient to **exclude every** C-conforming S′. Writer failure is never
  a certificate; a certificate that cannot establish nonexistence is never VO.
- **UR (unresolved).** Neither a valid witness nor a valid obstruction proof. Explicitly licenses
  nothing; absorbs every doubt, per the frozen error-flow property.

Round-2 J3 values do not appear anywhere in this pipeline.

## 2. Estimand

Sep(t) = 1 iff ∃ S′ satisfying **C** with: all capability cases of *t* determined per Definition D,
and no safety case determined per Definition D. σ = E[Sep(t)] over the **eligible subpopulation**
(§3). Identification: under **A-DS** (a both-runs-verified witness proves existence) and **A-VO**
(a verified certificate proves nonexistence under C), σ ∈ **[P(DS), P(DS)+P(UR)] = [P(DS),
1−P(VO)]**, sharp; without them, nothing narrows.

**Primary descriptive result (fixed by the CR-1 ruling message):** the **sample identification
region [P̂(DS), 1−P̂(VO)]** computed over the measured-eligible tasks. It is a descriptive
identification statement — a finite-sample logical consequence of A-DS/A-VO — and is **never
called, formatted, or interpreted as a confidence interval.** The estimand–estimator audit
(`c666d69c…`, sim `090b191e…`, results `567e9a1f…`) demonstrated it exact under the assumptions
(in-sample containment 1.0000 in every assumption-holding scenario, including the VO boundary and
low yield) and assumption-bearing rather than tautological (a negative fixture violating A-DS
drives containment to 0.0000).

Three uncertainty layers, named apart and never merged into any single overall interval:

1. **L0 identification width** — P̂(UR), the width of the sample identification region;
   irreducible by sample size.
2. **L1 sampling uncertainty** — exactly two **per-endpoint Clopper–Pearson 95% intervals,
   conditional on the realized m** (the measured-eligible count): one for π_DS, one for π_VO.
   The targets are **procedure-inclusive**: π_DS and π_VO are the rates the ⟨SRSWOR sampling,
   baseline screen, constructive procedure⟩ pipeline produces over the eligible subpopulation,
   superscripted to the frozen eligibility rule of §3 — not procedure-free properties of tasks.
   The SRSWOR finite-population correction is ignored, which is conservative. The audit adopted
   Clopper–Pearson on demonstrated coverage (≥ 0.968 everywhere, 1.000 at the π_VO = 0 boundary,
   holding at mean yield 19) and **rejected** the percentile bootstrap (π_VO coverage
   0.933–0.940). **No percentile-bootstrap endpoint CI, no Imbens–Manski interval, and no
   composite/combined overall interval of any kind is computed or reported.**
3. **L2 measurement sensitivity** — prespecified descriptive contrasts of the two blinded runs:
   the DS both-runs definition versus the either-run profile, and eligibility both-agree versus
   either-agree. These are sensitivity descriptives with their own named rows; **the either-run
   profile is never substituted for, or reported as, a confirmatory classification.** Study 1's
   [both, either] interval is measurement uncertainty about a point-identified θ; Study 3's
   sample identification region is an identification gap about a point σ. Same brackets,
   different epistemology, distinct names in every table.

**Role of the audit simulation, fixed:** the simulation validates estimator and procedure
properties only (containment and coverage under stated scenarios). It does not and cannot
establish the identification assumptions; **A-DS and A-VO are the substantive conditions under
which the bounds hold**, defended by their conservative constructions (both-runs witness profile;
decidable-certificates-only VO), not by simulation.

## 3. Task set and eligibility — selection/conditioning rule, pinned before any outcome is seen

- **Sampling frame:** the frozen Round-2 frame (864, sha `3840d50f…`) **minus** every
  prior-exposure set: the 90 Round-2/Study-1 tasks, the 10-task ordered reserve (identities
  revealed by the frozen selection), the 12 IDR1 tasks, and the feasibility-study tasks. All
  exclusions are enumerable from frozen manifests; the exclusion list is built mechanically
  (`scripts/build_study3_frame.py`) and frozen with the protocol as `2026-08-28_study3_frame.json`.
  Manifest arithmetic, verified at build: the 864 frame already excludes the 21
  development-exposure tasks of the Round-2 exclusion log, and the 12 feasibility-study tasks are
  index-identical to the 12 IDR1 tasks (both inside those 21), so the net Study-3 frame is
  864 − 90 − 10 = **764 tasks**; the IDR1/feasibility subtractions are idempotent, applied anyway.
  **The exclusion list and frame are fixed at freeze; no task is substituted, restored, or removed
  in response to the remaining frame's content or to any outcome.**
- **Fresh draw:** one SRSWOR draw of N = 90 (§9, CR-1 ruling), seed =
  `int(sha256(frozen protocol file)[0:8], 16)`; single draw, no reroll, no stratification on
  anything.
- **Eligibility (the conditional subpopulation, per the pre-committed RQ3) — verbatim rule, fixed
  a priori:** a drawn task enters the Study-3 analysis set iff its **baseline stage** — two fresh
  independent blinded J1 runs over its *original* S_t, the Study-1 machinery verbatim — finds
  **at least one safety case determined in both runs** (both-agree: the measurement-conservative
  rule). What this rule produces is **measured eligibility**: an outcome of the baseline
  measurement process, not a latent property read off the task. The realized eligible count **m is
  a result, never a design target**; per the CR-1 ruling, nothing reacts to it — no supplemental
  draw, no redraw, no extended recruitment, whatever m turns out to be. **If m = 0, every layer
  reports "no eligible tasks" and the study reports the baseline profiles alone — prespecified, no
  improvisation.** Ineligible tasks are reported as a count with their baseline profiles; they are
  the already-blind stratum, and σ is explicitly *conditional* on baseline determination.
- **Study-1 case-level outcomes never enter eligibility or selection.** The 90 tasks they exist
  for are excluded wholesale; for fresh tasks no Study-1 outcome exists. Baseline determination is
  measured inside Study 3, by a rule fixed in this section before any fresh-task outcome exists.

## 4. Constraint set C — transformation rules, pinned

Immutable, byte-identical between S and S′:
- the **setup/preamble block** (harness-executed; editing it changes the oracle);
- the **function name**;
- the **closing instruction sentence**;
- **every case** (inputs and expected behaviour; the oracle is untouched);
- the field schema: no new fields, no reordering.

Editable: the five prose fields (`description`, `context`, `arguments`, `return`, `raise`) —
clauses may be removed or rewritten — and the `security_policy` field, whose complete removal is
the canonical move. A parameter documented in `arguments` may be re-described but not dropped:
every parameter of the original must remain mentioned (mechanically checkable), so the interface
stays the same task.

Adequacy is **never** judged by the writer or the validator:
- **capability preservation** is established only by the blinded J1 evidence: all capability cases
  determined in both runs over S′;
- **safety underdetermination** likewise: no safety case determined in either run.
The validator (frozen before authoring) checks only mechanical invariants: schema, immutability of
the frozen components, parameter mentions, provenance hashes.

## 5. Data flow: writer → validator → blinded verification

1. **Writer** (fresh session; sees the original spec with case-kind labels — the blind boundary is
   set by the estimand, as in Round 2): for every task, ships its best candidate S′ **and**, where
   it hit a wall, a structured obstruction claim with quotations. No abstention: failure never
   drops a task, and a declared-failure task's candidate still proceeds — the writer's pessimism
   is data, not routing.
2. **Frozen validator**: mechanical invariants only (§4). Resubmission gates as in Round 2 if
   needed; identity-of-edit discipline inherited.
3. **Blinded witness check**: S′ packets built by the Study-1 builder machinery (verbatim reuse:
   presentation permutations, sentinel markers, fingerprints, quote-location validator); **two
   fresh independent blinded J1 runs** that never learn S′ is derived, that a baseline exists, or
   what any case kind is. They answer only bounded per-case questions — no verifier ever faces an
   existential question.
4. **Derivation, mechanical:** DS iff both runs' profiles show [all capability determined, no
   safety determined]. Writer obstruction claims and candidate S′ are both preserved in the frozen
   record regardless of outcome.

Baseline stage (§3) and witness stage use disjoint fresh coding sessions; no session codes both an
original and its derived S′.

## 6. VO certificate taxonomy and proof standards

Governing rule (fixed): **VO requires a certificate that excludes every C-conforming S′.** What
cannot prove nonexistence is UR. Writer failure codes alone are never VO.

- **VO-STRUCT — immutable-carrier determination.** Claim: a safety case is determined by text that
  survives in *every* C-conforming S′ (setup block, function name, closing instruction, or the
  mandatory parameter mentions). Since the carrier is immutable under C, determination transfers
  to all S′, so Sep(t)=0. **Verification is mechanical given the blinded evidence:** in both
  baseline runs the safety case is determined with quotes locating **only** in immutable
  components (the Study-1 quote-location machinery). No new semantic layer.
- **VO-DEFECT — material incoherence.** Claim: the task's immutable components and cases are
  mutually contradictory, so no C-conforming specification is functionally sufficient at all.
  Standard: the certificate quotes the contradicting elements; an independent verification role —
  fresh session, sees only the certificate and the immutable materials, never the J1 runs — must
  confirm the contradiction from the quotes alone. Expected rare.
- **Coupling claims (F1 heritage) are not VO.** A claim that every capability-sufficient phrasing
  settles a safety case asserts a universal over unbounded phrasings; no pre-defined decidable
  standard verifies it. Coupling claims are recorded, reported descriptively beside the Round-2
  writer-channel evidence, and the task lands **UR**. This widens the band — the honest direction
  — and makes P(VO) a conservative lower bound on inseparability.

DS∧VO on the same task is the frozen instrument-defect halt: interpretation stops, nothing is
reconciled silently.

## 7. Reporting

Over the measured-eligible tasks: counts and shares P̂(DS), P̂(VO), P̂(UR) with the **sample
identification region [P̂(DS), 1−P̂(VO)]** (a descriptive identification statement; not a
confidence interval). **L1:** exactly two Clopper–Pearson 95% intervals conditional on the
realized m — one for π_DS, one for π_VO. **No percentile-bootstrap endpoint CI, no Imbens–Manski
interval, and no combined overall interval is computed or reported.** **L2:** the
measurement-sensitivity contrasts of §2, in their own named rows, never pooled into L0/L1 and
never reported as confirmatory classifications. One table, three named layers, no merging.
Also reported: baseline eligibility rate and realized m (a result, not a target; m = 0 branch per
§3); ineligible count with baseline profiles; per-run and both-agree witness-check profiles;
writer declaration distribution; coupling-claim counts (descriptive); the DS witnesses themselves
— the blinded specifications — released as the artifact deliverable. No metric beyond this list;
no threshold anywhere.

## 8. What Study 3 never does

Reuses the 90 development tasks in the analysis set; treats any Round-2 J3 value as an outcome,
eligibility input, or inference input (J3 appears only as instrument-development rationale); asks
any coder an existence question; scores DS from writer success or VO from writer failure;
adjudicates run disagreements; runs any model-evaluation API — no model API evaluation is a
Study-3 outcome, and Study 4 remains closed.

## 9. Conditioning-risk register — all entries closed at freeze

- **CR-1 (CLOSED by ruling, 2026-08-28).** **Resource-fixed one-stage sampling.** Baseline sample
  size fixed at **N = 90 tasks**, justified solely by the a-priori resource budget and the
  double-blinded coding batch scale already demonstrated executable — **not** described as
  power-derived or precision-derived. One SRSWOR draw of 90 from the frozen Study-3 eligible
  frame; baseline double-blinded J1 on all 90; every task meeting the frozen eligibility rule
  proceeds to the constructive stage. **Whatever the eligible yield, no supplemental draw, no
  redraw, no extended recruitment.** Study-1 θ and every other Study-1 outcome value are barred
  from Study-3 selection, sample-size, eligibility, and stopping logic; outcome-dependent
  supplemental sampling is barred.
- **CR-2 (closed — documented).** The conditional-subpopulation estimand might look θ-informed; it
  is not: RQ3's conditional wording is frozen in the architecture draft, which predates every
  Study-1 outcome. Recorded to preempt the reviewer version of this question.
- **CR-3 (closed — documented).** Verbatim reuse of Study-1 tooling is procedural transport, not
  outcome transport; the data-flow audit pattern extends to Study-3 tooling when built.
