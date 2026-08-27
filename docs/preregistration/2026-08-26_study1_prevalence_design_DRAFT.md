# Study 1 — Formal determination prevalence: design (DRAFT, nothing executed)

**Status.** Design for a decision. Not a frozen protocol: no packet is built, no run is started, no
benchmark sample is drawn, no case is coded. *Revised 2026-08-27: §3's `security_policy` secondary
analysis restated as a partial-identification estimand; §6's second-benchmark question resolved by
an outcome-blind compatibility table. Design principles accepted by decision of 2026-08-27; freeze
still pending.* Where the design depends on a fact not yet verified at
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
- **Prespecified secondary (`security_policy` analysis), stated strictly.** The instrument records
  **one quote per determined case** — a single witness of obligation, not an exhaustive inventory of
  carriers. Quote location therefore supports claims about *citation*, never about *unique source*,
  and the analysis is worded and computed accordingly:
  - Mechanical classes over determined safety cases, by the frozen normalised-containment rule,
    multi-field location allowed: **(a)** the quote locates only in `security_policy`; **(b)** the
    quote locates in at least one field other than `security_policy` (whether or not it also locates
    there); (c) not locatable — excluded by the new validator check.
  - The quantity of interest — *the fraction of determined safety cases whose determination would
    survive removal of the `security_policy` field* — is **partially identified** by these classes:
    - **lower bound = class (b) rate**: the cited obliging sentence persists verbatim after removal,
      under a stated modularity assumption (the persisting sentence retains its obliging force when
      `security_policy` is deleted);
    - **upper bound = 1**: a policy-only citation does not show that no other field determines the
      case — the single-quote design cannot rule out redundant carriers.
  - Equivalently, the benchmark's own ablation switch can remove **at most** the class-(a) fraction
    of determined safety cases; that "at most" is the formal successor of the exploratory ~14%
    finding, and is the only directional claim made.
  - Point-identifying the survival fraction would require a second blinded coding pass on
    policy-ablated specifications — a different study, explicitly not part of Study 1.
  - Language discipline throughout: quotes *cite* and *locate*; they are never described as the
    *cause* or *the source* of determination. Reported per run, with a both-agree conservative
    variant; descriptive, no confirmatory threshold.

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

**Outcome-blind compatibility table (assessed 2026-08-27).** Each cell records a structural fact of
the shipped harness, verified at source; no specification content was read for leakage, and
prominence played no part. CyberSecEval is judged on its secure-code-generation suites
(instruct/autocomplete), the ones cited as its secure-coding measurement.

| structural check | CWEval | CyberSecEval (PurpleLlama) | BaxBench |
|---|---|---|---|
| model-visible S exists | **yes** — function signature + docstring (task file above `BEGIN SOLUTION`) | yes — instruction prompt | yes — `api_spec` + `text_spec` + `scenario_instructions` |
| case-level oracle behaviour *b* | **yes** — `pytest.param(inputs…, expected_output)` lists; per-input expected outputs, side-condition asserts included | **no** — oracle is `insecure_code_detector` static patterns over emitted text; no execution, no behaviour at an input | partial — `functional_tests` / `security_tests` are bool-returning *procedures* against a live app; *b* must be extracted from each test body by a frozen rule, not read off a declared expected output |
| benchmark's own security/functionality metadata | **yes** — shipped `pytest.mark.functionality` / `pytest.mark.security` marks | **no** — no functional oracle exists at all, so no such distinction | yes — separate `functional_tests` and `security_tests` fields |
| Definition D applies unchanged | **yes** — ⟨docstring-spec, expected output at input *i*⟩, the SeCodePLT shape; witness = shipped reference solution, and the harness already encodes the Gate-2 self-check (reference passes all, unsafe variant must fail security cases) | **no** — D is defined over oracle *behaviour*; a lint pattern over code text is a different construct (determination of code shape, not of behaviour) | strained — construct arguably unchanged, but the case unit is a procedure and *b* is implicit in assertion code; application needs an extraction layer that is itself a fresh instrument decision |
| task-clustered case-level prevalence estimand | **yes** — cases within task files; clustering rule to freeze: language variants of one task share spec content, so cluster = task family (or restrict the frame to `core/py`) | no — no cases | weak — specs are identical across the 14 frameworks, so the effective sample is 28 scenario clusters with ~1 functional + 1–3 security procedures each; the estimand exists but with very low precision |
| B2 development independence | yes — no part in developing Definition D or any protocol | yes (fails on B1, not B2) | **no** — AutoBaxBuilder *is* a BaxBench-format generator; the programme's exploratory origin (spec-grounding 89–91%, entanglement 35%, the 08-06/08-17 protocols) ran on this task family and harness |
| B5 prior exposure to declare | structural classifier over all 119 test files (the 62/119 count); the `cwe_943_0` family read at case level during the classifier audit and this scan — **excluded from any formal frame** | structural audit only | extensive and disqualifying (see B2) |

**Ruling.** Only **CWEval** satisfies B1–B5; if a second formal benchmark is added, it is CWEval, and
the `cwe_943_0` family is excluded from its frame as examined material. **CyberSecEval fails B1 on
three of five checks and is assigned to complementary characterization** — its prominence does not
buy back a missing case-level oracle, and forcing D onto a linter would change the construct.
**BaxBench is assigned to complementary characterization / origin material**: even setting aside the
extraction-layer strain on B1, its entanglement with our own generator lineage (B2/B5) would turn a
"transportability" claim circular — it is the family the construct was discovered on. Whether to
*run* CWEval as the second formal benchmark remains **deferred** and does not gate Study 1.

## 7. Execution order (when approved — not now)

freeze eligibility ruling + extraction rule (incl. the setup-visibility verification) → freeze
packet builder, validator, analysis code, this design as protocol → build packets → isolation
preflight → two blinded runs → validate + freeze both submissions → reveal, align, score with
pre-committed code. Any deviation is recorded, never patched silently.
