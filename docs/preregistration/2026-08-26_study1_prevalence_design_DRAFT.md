# Study 1 — Formal determination prevalence: design (DRAFT, nothing executed)

**Status.** Design for a decision. Not a frozen protocol: no packet is built, no run is started, no
benchmark sample is drawn, no case is coded. Where the design depends on a fact not yet verified at
source, that fact is flagged as a **freeze-time verification item** rather than assumed. Companion
to the architecture draft (`e3fcad18…`) and the interpretation memo (`8aef7785…`).

---

## 1. Sample: reuse the frozen 90 tasks, coding their original specifications

**Recommendation: yes — reuse, with the argument made explicitly and frozen.**

Why reuse is valid:

- The 90 were drawn by frozen seed (`int(PROTOCOL_SHA[:8],16)`) from the eligible frame of 864,
  **before any specification was authored and blind to every subsequent outcome**. As a random
  sample of the frame they are exactly as good today as on the day of the draw; nothing about the
  draw was conditioned on any J1/J2/J3 result.
- **Their original specifications have never been coded by any run.** Round 2's coders saw only the
  writer's candidates S′. Two fresh blinded runs on the originals are prospectively blind at the
  coder level.
- The memo §5.2 restriction is scoped: the 90 are spent as a prospective validation sample *for
  constructibility measurement*. Study 1 measures J1 prevalence on different texts (the originals).
  The protocol must state this eligibility ruling affirmatively, so it is a recorded decision and
  not a silent assumption.
- Reuse burns no additional slice of the pool, and keeps Study 1 inside the standing instruction:
  no new benchmark sampling.

What reuse costs, and the controls:

- **The analyst is not blind.** We have seen the S′ judgements and the writer's `edits[]`, which
  identify clauses of the originals that carry determination. Control: zero post-run analyst
  degrees of freedom — packets built mechanically from benchmark records by frozen code, the entire
  analysis (estimators, strata, exclusion rules, reporting tables) committed before either run
  starts, exactly the Round-2 discipline.
- **Reviewer optics** ("reliability sample = prevalence sample"): the texts differ (S′ vs originals),
  and Study 1 computes its own agreement on originals (§4), so the reliability claim for Study 1 is
  self-contained rather than borrowed.
- **Transfer caveat, stated not hidden:** Round 2's κ 0.804 was earned on S′ — related but not
  identical text distribution (originals carry `security_policy` prose and are plausibly *easier*).
  Round 2 therefore functions as prior evidence that the primitive is codable, and Study 1's own
  two-run agreement is the reliability figure for prevalence.

## 2. Separation from Study 2's S′ judgements

Six mechanisms, all checkable:

1. **Build path.** The Study-1 packet builder reads only benchmark records (via the frozen task
   runner's loader). It never imports, opens, or transits any writer artifact; the writer package,
   accepted submission, and Round-2 packets are not inputs to any Study-1 script.
2. **ID namespace.** Fresh blinded task IDs under a new prefix and a new presentation seed; no ID
   collides with Round-2 `C…` IDs or writer `W…` IDs. The new sealed key maps Study-1 IDs directly
   to benchmark indices.
3. **Data-flow rule, frozen in code.** Study-1 analysis reads only Study-1 submissions and the
   Study-1 key. It never reads Round-2 submissions, the writer output, or Round-2 results. (The
   converse quarantine too: no Round-2 document is amended to cite Study-1 numbers.)
4. **Reporting separation.** Original-vs-S′ paired contrasts — scientifically tempting with reused
   tasks — are **exploratory Study-3 development evidence**, produced (if at all) in a separate
   document after Study 1's confirmatory report is frozen. Study 1's confirmatory outputs contain
   zero quantities computed from any S′ judgement.
5. **Coder blinding.** Fresh isolated sessions with the Round-2 startup-prompt discipline: coders
   are not told these tasks relate to any prior study, that blinded variants exist, or what the
   research question is; only frozen wording may be repeated to them.
6. **Isolation preflight.** The frozen Round-2 preflight pattern re-run for the two new directories.

## 3. Estimand — precise definition

**Population.** The eligible SeCodePLT frame (864 tasks) under the frozen Round-2 eligibility rules.

**The measured object.** For task *t*, the specification *S_t* is **the benchmark's default
model-facing prompt content**: the seven `task_description` fields (`function_name`, `description`,
`security_policy` — which ships on by default — `context`, `arguments`, `return`, `raise`) as the
benchmark's default template renders them, plus the function signature.
*Freeze-time verification item:* whether the default prompt also shows the `unittest.setup` code
must be verified against the benchmark's own eval code, and the extraction rule frozen accordingly.
The estimand is *the benchmark as shipped*, so nothing the model is shown may be dropped and nothing
it is not shown may be added.

**Parameter.** For case *i* of task *t* (the benchmark's own `capability` / `safety` labels), let
D(t,i) ∈ {0,1} be determination of the oracle behaviour at *i* by *S_t* per frozen Definition D.
The estimands are case-weighted rates over the population:

- **θ_saf** — determination rate over safety cases: the headline. *The fraction of security oracle
  behaviours that the shipped specification itself obliges.*
- **θ_cap** — over capability cases: reported as context (functional determination is what a
  specification is *for*; high θ_cap is expected and is not the defect).
- **θ_all** — overall.
- Secondary, derived and labelled brittle: task-level P(any safety case determined).
- **Prespecified secondary (carrier split):** among determined safety cases, the fraction whose
  quotes locate (mechanically, by the frozen normalised-containment rule) **only in
  `security_policy`** versus elsewhere. This upgrades the exploratory "one-line ablation blinds only
  ~14%" finding to formal grade: it is exactly the fraction of determination the benchmark's own
  switch could remove.

**Measurement rule without adjudication.** Two runs, no consensus step:

- per-run rates for every parameter;
- prespecified primary point estimate = the two-run mean;
- a **measurement-disagreement interval**: [rate counting only cases both runs call determined,
  rate counting cases either run calls determined]. This is measurement uncertainty around a
  point-identified parameter — deliberately named differently from Study 3's identification bounds
  (see the companion note) to prevent conflation;
- 95% CIs on all of the above by task-level cluster bootstrap (2000 reps, frozen machinery).

## 4. Coding design

- **J1 only, plus the C6 `confidence` field.** J3 is retired; J2 is unnecessary for prevalence and
  is dropped (less coder load, nothing lost for RQ1).
- **Wording: frozen v2 J1 text and Definition D, verbatim.** The validated instrument transfers by
  identity of the question, the definition, the quote requirement, and the answer format; only the
  packet contents change. One addition closes a recorded Round-2 instrument gap: the submission
  validator additionally checks that **every quote locates in the presented specification** (the
  five non-locatable quotes of Round 2 motivate this; it is a schema-level check, not semantic).
- Two independent blinded runs, identical packets, per-run presentation permutations, frozen answer
  template — the Round-2 shape throughout.
- Study 1 reports its own raw agreement and cluster-aware κ on originals, as internal reliability.

## 5. Inference and sample-size justification

Fixed by reuse: 90 tasks, 442 cases (237 capability, 205 safety; mean 4.9 cases/task, safety mean
2.28/task). Precision, computed with Round-2 ICCs as planning values (0.41/0.36, from S′ coding —
planning values only):

| stratum | n cases | planning ICC | effective n | worst-case 95% half-width (p=0.5) |
|---|---|---|---|---|
| overall | 442 | 0.40 | ≈172 | ±0.075 |
| safety (headline) | 205 | 0.20 | ≈163 | ±0.077 |
| safety | 205 | 0.40 | ≈136 | ±0.084 |
| safety | 205 | 0.60 | ≈116 | ±0.091 |

Adequacy statement, prespecified: the design supports claims at the grade of "θ_saf is near 0.3 vs
near 0.5 vs near 0.8" — **no confirmatory claim finer than ±0.10 will be made**, and the paper's
argument (§0 of the architecture) needs none. If θ_saf lands so close to a rhetorically loaded
boundary that ±0.09 straddles it, the number is reported with its interval and no boundary language.

## 6. Second formal benchmark

**Not required for the minimal publishable version.** The central claim is measurement-theoretic;
industry-wide *structure* is carried by the frozen exploratory tier (CWEval 62/119 shared oracles,
PurpleLlama's linter-as-oracle, SeCodePLT's ablation gap), and the formal prevalence claim is
explicitly scoped to SeCodePLT. Overclaiming, not single-benchmark scoping, is the error to avoid.

**Recommended as the single best generality hardening**, for a reason beyond optics: Definition D
and the v2 wording were developed against SeCodePLT material (the 90 were held out, but the
*instrument's language* evolved on that benchmark), so a second benchmark is a transportability
test. It would carry its own two-run reliability estimate — self-contained, like Study 1's.

**Ex-ante selection criteria — frozen before inspecting any candidate's specifications, and none of
them mentions leakage:**

- **B1 Structural compatibility.** A model-facing specification; an executable case-level oracle;
  security-relevant vs functional checks distinguished by the benchmark's **own shipped metadata or
  naming** (never by our judgement of content).
- **B2 Development independence.** Took no part in developing Definition D or any protocol version.
- **B3 Prominence.** Selected by adoption/citation figures recorded *before* the choice.
- **B4 Witness availability.** A reference solution exists and the harness runs, so the Gate-2-style
  constructive self-check is possible.
- **B5 Prior-exposure disclosure.** Everything already examined about a candidate is declared at
  selection time. For CWEval that is the frozen structural count (62/119) — structural, never
  per-case coding. For PurpleLlama, its structural audit.

Applied today: CWEval satisfies B1–B5 (B1 via its own `_test_functionality` / `_test_security`
split); PurpleLlama fails B1 (no functional oracle; the linter is the oracle). The decision to add
a second benchmark is **deferred** and does not gate Study 1.

## 7. Execution order (when approved — not now)

freeze eligibility ruling + extraction rule (incl. the setup-visibility verification) → freeze
packet builder, validator, analysis code, this design as protocol → build packets → isolation
preflight → two blinded runs → validate + freeze both submissions → reveal, align, score with
pre-committed code. Any deviation is recorded, never patched silently.
