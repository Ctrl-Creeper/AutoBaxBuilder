# Study 3 — Constructive separability: protocol DRAFT (nothing executed)

**Status.** Draft for a decision, produced by design reconciliation only. No task outcome is
generated, no sample is drawn, no writer or coder session exists, no API evaluation runs. Two
conditioning risks are flagged and **left undecided** (§9); the draft cannot be frozen until they
are ruled on.

---

## 0. Design reconciliation — what is already committed, and where

Recovered verbatim-in-substance from frozen documents; nothing below is new:

| commitment | source |
|---|---|
| Study 3 measures constructive separability via an evidence-producing procedure with outcomes DS / VO / UR; annotation of existence claims is retired | architecture draft `e3fcad18…` §3; J3 analysis `fa9fe398…` Part I |
| σ = E[Sep(t)] defined via Definition D and a frozen constraint set **C**, independent of the procedure; identified set **[P(DS), 1−P(VO)]**, sharp under A-DS/A-VO; UR assumption-free; all hesitation flows into UR; Imbens–Manski-style inference | PI note `743da509…` §§1–4 |
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
  safety case is determined. The witness — S′ itself — is the deliverable.
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

Three uncertainty layers, named apart and never merged:

1. **identification width** — P(UR), irreducible by sample size;
2. **sampling uncertainty** — Study 3 samples its subpopulation (unlike CWEval's census), so
   task-cluster bootstrap CIs on both endpoints are legitimate finite-population-directed
   inference here, combined Imbens–Manski-style;
3. **measurement uncertainty** — the two J1 runs' disagreement, reported Study-1-style
   ([both, either] on the underlying case rates). Study 1's [both, either] interval is
   measurement uncertainty about a point-identified θ; Study 3's [P(DS), 1−P(VO)] is an
   identification gap about a point σ. Same brackets, different epistemology, distinct names in
   every table.

## 3. Task set and eligibility — selection/conditioning rule, pinned before any outcome is seen

- **Sampling frame:** the frozen Round-2 frame (864, sha `3840d50f…`) **minus** every
  prior-exposure set: the 90 Round-2/Study-1 tasks, the 10-task ordered reserve (identities
  revealed by the frozen selection), the 12 IDR1 tasks, and the feasibility-study tasks. All
  exclusions are enumerable from frozen manifests; the exclusion list is built mechanically and
  frozen with the protocol.
- **Fresh draw**, seed derived from this protocol's hash at freeze; single draw, no reroll, no
  stratification on anything.
- **Eligibility (the conditional subpopulation, per the pre-committed RQ3):** a drawn task enters
  the Study-3 analysis set iff its **baseline stage** — two fresh independent blinded J1 runs over
  its *original* S_t, the Study-1 machinery verbatim — finds **at least one safety case determined
  in both runs** (both-agree: the measurement-conservative rule, fixed here a priori). Ineligible
  tasks are reported as a count with their baseline profiles; they are the already-blind stratum,
  and σ is explicitly *conditional* on baseline determination.
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

P(DS), P(VO), P(UR) with the identified set [P(DS), 1−P(VO)]; endpoint bootstrap CIs
(task-cluster, seed from protocol hash) combined Imbens–Manski-style; per-run and both-agree
witness-check profiles; baseline eligibility rate; writer declaration distribution; coupling-claim
counts (descriptive); the DS witnesses themselves — the blinded specifications — released as the
artifact deliverable. No metric beyond this list; no threshold anywhere.

## 8. What Study 3 never does

Reuses the 90 development tasks in the analysis set; treats any Round-2 J3 value as an outcome;
asks any coder an existence question; scores VO from writer failure; adjudicates run
disagreements; runs any model-evaluation API.

## 9. Conditioning-risk register — flagged and stopped, not chosen

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
