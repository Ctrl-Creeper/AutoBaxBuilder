# Paper architecture v1

**Document type:** frozen-artifact synthesis, not a preregistration.  
**Evidence cutoff:** Study 3 final freeze `8c39ad48f90f1369bf8729b3585cb17079349042`.  
**Scope:** no new data, no task-level reanalysis, and no Study-4 result.

## Central thesis and claim boundary

Within SeCodePLT, model-visible task specifications frequently determine the security-oracle
behaviour that the benchmark later scores. Determination is measurable with a prospectively frozen,
quotation-grounded instrument, and much of it is constructively removable for the realized
measured-eligible confirmatory sample while preserving capability determination. Consequently, a
security score on such cases cannot by itself distinguish spontaneous security behaviour from
compliance with an explicit requirement. This is a construct-validity threat, not a demonstrated
estimate of score inflation.

The paper does **not** claim that all security benchmarks have this prevalence, that every task is
separable, that no obstruction exists, or that models actually exploit the determining information.

## 1. Motivation and construct problem

Frame the measurement problem using the distinction between ordinary functional specification
following and the security capability a security benchmark is intended to isolate. If the
model-visible specification already obliges the exact security-oracle behaviour, passing the test
is compatible with both constructs. The benchmark response is therefore not diagnostic between
them.

Use the previously frozen AutoBaxBuilder/BaxBench/CWEval/PurpleLlama structural work only as
motivation and complementary characterization. It must not be presented as a common Definition-D
prevalence estimate across benchmarks.

**Primary contribution introduced here:** a claim-evidence discipline that separates (a) existence
and prevalence of determination, (b) reproducibility of its measurement, (c) constructive
removability, and (d) the unmeasured causal consequence for model scores.

## 2. Definition and measurement

Introduce Definition D at the case level:

> A specification `S` determines behaviour `b` at input `i` when a competent implementer reading
> only `S`, without the test suite, would be obliged to produce `b`; any alternative would contradict
> an identifiable sentence of `S`.

Both frozen restrictions are load-bearing: a determined judgment requires a locatable quotation,
and reaching the behaviour permits at most one inferential step with no external knowledge.

Place **Study 2** here as the prospective validation of J1, and only J1:

- 90 tasks and 442 cases; two independent blinded coding runs;
- raw agreement `0.937`;
- primary task-cluster-aware kappa `0.804`, 95% CI `[0.708, 0.893]`;
- pooled kappa `0.869` is descriptive only;
- AC1 `0.877`, 95% interval `[0.808, 0.936]`, is sensitivity only;
- tie-break rates were `18.8%` and `24.0%`.

The text must say **independent blinded coding runs**, not independent human coders. Shared model or
prompt lineage leaves correlated error possible.

The J3 failure belongs in the main text: both runs returned the existential answer `true` for all
90 tasks. A constant response supplies no discriminative reliability evidence. Study 2 therefore
validated the Definition-D/J1 measurement primitive, not constructibility annotation or the earlier
five-class taxonomy.

Put full prompts, schemas, cluster-bootstrap mechanics, pooled-kappa rationale, ICCs, quote
concordance, and disagreement diagnostics in the appendix.

## 3. Original-specification prevalence

Place **Study 1** here. Its estimand is case-weighted determination in the eligible SeCodePLT frame
of 864 tasks, measured on a frozen random sample of 90 tasks containing 442 cases (237 capability,
205 safety). `S_t` is the benchmark's shipped model-visible prompt with
`include_security_policy=True`.

Headline estimates:

| Estimand | Two-run mean | Measurement-disagreement interval | Task-cluster bootstrap 95% CI |
|---|---:|---:|---:|
| `theta_saf` | `0.7805` | `[0.7707, 0.7902]` | `[0.7040, 0.8492]` |
| `theta_cap` | `0.6899` | `[0.6751, 0.7046]` | `[0.5964, 0.7813]` |

Study 1's internal reliability on original specifications was raw agreement `0.9751` and
task-cluster-aware kappa `0.8689`, with bootstrap 95% CI `[0.7657, 0.9685]`.

The `security_policy` quote-location analysis is partial identification, not source attribution.
Among determined safety cases, the lower bound on survival after removing only the
`security_policy` field was `0.8428` in run 1 and `0.7205` in run 2; the conservative both-agree
variant was `0.7215`. Equivalently, that switch could remove at most `0.1572` and `0.2795` of the
respective runs' determined safety cases. Quotes locate one witness; they do not prove a unique
cause or carrier.

Keep the case-weighted estimand explicit. Do not rewrite `theta_saf` as the share of tasks, the
whole benchmark, or benchmarks in general.

## 4. Constructive separability

Place **Study 3** here as an evidence-producing procedure, not an annotation exercise. Its
population is the realized measured-eligible confirmatory sample. A task is demonstrated separable
(DS) only when both blinded verification runs find that the produced candidate specification
determines every capability case and no safety case. Verified obstruction (VO) requires a valid
frozen sufficient certificate; all other states are unresolved (UR).

Frozen result:

- measured-eligible confirmatory `m = 53`;
- `DS = 47`, `VO = 0`, `UR = 6`, procedure-invalid `= 0`;
- L0 sample identification region `[47/53, 1] = [0.8868, 1]`;
- separate L1 Clopper-Pearson 95% endpoint intervals: `pi_DS [0.7697, 0.9573]` and
  `pi_VO [0, 0.0672]`;
- preregistered L2 measurement sensitivity: both-runs DS share `0.8868`, either-run DS share
  `0.9811`; both-agree eligibility `53`, either-agree sensitivity count `56`.

L0 identification uncertainty, L1 sampling uncertainty, and L2 measurement sensitivity must remain
visually and verbally separate. The 88.7% figure is conditional on measured eligibility and is not
a prevalence estimate for the full benchmark.

Disclose the execution history in the main text: Writer Run 1 ended in a frozen
`WRITER_INSTRUMENT_CONTRACT_FAILURE`; the bounded repair was frozen without using candidate
substance; fresh Run 2 returned `ACCEPT_FIRST_RUN2` and became the sole formal constructive path.
Give the full GAP-6/GAP-8 manifests and interface audit in the appendix.

Also disclose in the main text that VO-DEFECT was permanently closed because the frozen instrument
lacked a sufficiently operationalized independent evidence-production and attestation procedure.
`VO = 0` therefore means that no obstruction was established by the valid frozen VO procedure, not
that no obstruction exists. Detailed VO audit history belongs in the appendix.

## 5. Cross-benchmark portability and limitations

Report the **CWEval preregistered replication** as attempted and terminated before outcome
observation. The frozen case object could not be mechanically recovered across the frame because
83% of security cases used oracle representations requiring a new, unfrozen semantic extraction
layer. No CWEval Definition-D prevalence may be reported.

Allowed complementary characterization includes the frozen A/B/C oracle-representation counts
(16/39/59 files and 32/44/110 security cases) and the earlier structural classifier record, clearly
labelled as representation structure rather than specification leakage. The termination supports
one claim: the measurement interface does not automatically transport across oracle
representations. It does not show that CWEval has more, less, or equal determination.

Collect the remaining limitations here: formal prevalence is SeCodePLT-only; coding runs are not
human coders; Study 3 is conditional on measured eligibility; its upper endpoint is uninformative
because no valid VO certificate was established; and the constructive writer procedure provides a
lower bound rather than an exhaustive search.

Put detailed CWEval exposure ledgers, frame construction, termination gates, and other benchmarks'
structural tables in the appendix.

## 6. Discussion and implications

The defensible implication is methodological: benchmark designers should state whether security
tests are intended to measure compliance with disclosed requirements, spontaneous security
behaviour under underspecified requirements, or both. Where the intended construct requires the
second, model-visible oracle-determining text is a source of construct contamination. Definition-D
audits and constructively blinded specifications provide concrete diagnostics and repair artifacts.

Close by separating the unanswered behavioral question: Studies 1-3 do not estimate how much
model security-pass rates change when determination is removed. That causal estimand is a possible
Study 4 and an important enhancement, but it is not necessary for the scoped measurement-validity
claim established here.

## Evidence anchors

- `docs/preregistration/2026-08-27_study1_prevalence_protocol.md`
- `docs/preregistration/2026-08-27_study1_execution/results_study1_prevalence.json`
- `docs/preregistration/2026-08-25_instrument_validation_protocol_v2.md`
- `docs/preregistration/2026-08-26_round2_interpretation_memo.md`
- `docs/preregistration/2026-08-28_study3_execution/FINAL_STUDY3_RESULT_SUMMARY.json`
- `docs/preregistration/2026-08-28_study3_execution/GAP6_REPAIR_RECORD.md`
- `docs/preregistration/2026-08-28_study3_execution/VO_STRUCT_EXECUTABILITY_AUDIT.md`
- `docs/preregistration/2026-08-28_cweval_replication/AMENDMENT_1_gap2_termination.md`

