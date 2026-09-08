# Study-4 decision memo

**Document type:** frozen-artifact synthesis and decision support, not a preregistration.  
**Revision:** 2. Revision 1 was frozen at commit `1dda9cf5b3abdca8930900fdc8ac0d92234bb3b8`.  
**Evidence cutoff:** Study 3 final freeze `8c39ad48f90f1369bf8729b3585cb17079349042`, extended by
the frozen Study-4B and Study-4C-EX closures.  
**Decision constraint:** Study 3's 53 confirmatory tasks remain closed to new task-level,
failure-level, subgroup, or explanatory analysis.

**Reading order.** Sections up to "Recommendation" are the *ex ante* decision analysis, preserved
unchanged from revision 1 so that the decision can be judged on what was known at the time. What
actually happened afterwards is recorded in the final section, "Post-decision record". Do not read
the ex ante sections as descriptions of executed work.

## Decision in one sentence

Studies 1-3 already support a complete, scoped measurement/construct-validity paper. Study 4 would
add a different causal estimand about model behaviour; it is an important enhancement, not a
validity requirement. The recommended decision is **Version A: stop now**.

## Q4-1: Are Studies 1-3 sufficient for the central claim?

**Yes, with explicit population and evidence-grade limits.** The proposed central claim is:

> Security-benchmark construct validity is threatened when oracle behaviour is determined by the
> model-visible specification, and much of this determination is constructively removable.

Study 1 establishes that determination is frequent for SeCodePLT safety cases in a frozen random
sample (`theta_saf = 0.7805`, task-cluster bootstrap 95% CI `[0.7040, 0.8492]`). Study 2 establishes
prospective run-level reproducibility of Definition D/J1 (cluster-aware kappa `0.804`, 95% CI
`[0.708, 0.893]`). Study 3 establishes constructive removability for `47/53` of the realized
measured-eligible confirmatory sample, with the L0 sample identification region `[47/53, 1]`.

Together these answer existence, prevalence, measurability, and constructive separability. The
claim must remain SeCodePLT-scoped for formal prevalence, conditional on measured eligibility for
Study 3, and must not imply actual model use.

## Q4-2: What unique estimand would Study 4 add?

**A causal behavioral estimand:** the change in model security-pass behaviour caused by removing
oracle-determining information, alongside a prespecified capability-preservation check. In compact
form, the new object is a paired contrast such as

`Delta_sec = E[Y_sec(S) - Y_sec(S_prime)]`, with capability performance reported separately.

Studies 1-3 do not estimate this quantity. Constructive removability proves that a cleaner
measurement condition exists; it does not prove that a particular model noticed, used, or benefited
from the removed information.

## Q4-3: What can a reviewer deny without Study 4?

A reviewer cannot reasonably dismiss the scoped measurement-validity problem merely because the
behavioral effect is unmeasured. When the same observed pass is compatible with explicit
requirement compliance and spontaneous security behaviour, the score alone cannot identify which
construct produced it. That non-identification is present before measuring model uptake.

A reviewer can reasonably say that the paper does **not quantify practical score inflation**, does
not show that current models exploit the information, and does not estimate how the effect varies
by model. Those are behavioral-consequence claims, not prerequisites for the validity diagnosis.

## Version A: Stop now

**Paper delivered.** A measurement/construct-validity paper with four linked results:

1. a quotation-grounded Definition-D instrument;
2. prospective blinded run-level reliability;
3. formal SeCodePLT original-specification prevalence;
4. constructive separability with honest DS/VO/UR partial identification.

The CWEval termination becomes a principled portability limitation, not a failed prevalence result.

**Supported central wording:** model-visible security-oracle determination is common at the case
level in SeCodePLT, can be measured reproducibly by independent blinded coding runs, and was
constructively removed while preserving capability determination for `47/53` measured-eligible
confirmatory tasks. These facts create a construct-validity threat because affected scores cannot,
by themselves, separate requirement following from spontaneous security behaviour.

**Claims abandoned:** models exploit the information; scores are inflated; the size or direction of
any score effect; formal prevalence outside SeCodePLT; whole-benchmark separability; absence of
obstruction.

**Cost and risk:** no new data, API drift, task exposure, multiplicity, or reopening of the closed
Study-3 sample. The main risk is reviewer demand for practical effect size, handled by an explicit
claim boundary rather than an unsupported answer.

## Version B: Minimal Study 4

**Question answered.** Does removing determination change one frozen model's security-pass behaviour
while preserving capability performance in a prospectively defined population?

**Minimum defensible design shape:** a fresh task sample, because the 53 Study-3 confirmatory tasks
are closed to further task-level analysis; one prespecified model/version; paired original versus
constructively blinded specifications; identical harness and decoding policy; randomized
presentation; and a frozen capability-preservation criterion. All eligible tasks must enter without
selection on generated outcomes.

**API budget:** for `N` fresh tasks and `r` completions per specification condition, the model-eval
budget is `2 * N * r` generations. The literal execution floor is `2 * N` at `r=1`, but that is a
feasibility floor, not automatically a defensible estimate of stochastic model performance. No
exact `N` or `r` is identifiable from Studies 1-3 alone: a later preregistration would have to set a
smallest scientifically relevant paired effect, variance assumptions, power, model, token limits,
and attrition rule before fixing the number. Quoting a numerical minimum now would invent an
unfrozen assumption.

**New scientific value:** directly upgrades C9 from unsupported to tested for one model and one
frozen manipulation, and quantifies practical score consequences in that scope.

**Risks:** the fresh constructive pipeline is costly; capability preservation is a joint condition,
not a free assumption; model stochasticity may dominate a small paired effect; a single model can
date quickly; and prompt variants may introduce changes beyond determination unless audited.

## Version C: Full Study 4

**Question answered beyond Version B.** Whether the behavioral effect generalizes across models and
whether it depends on explicit security framing rather than merely on the presence of determining
content.

A full design would add multiple prespecified model families and a 2-by-2 manipulation of
determining information present/absent by security framing present/absent, with repeated generations
and capability outcomes evaluated from the same outputs. With `M` models, `N` fresh tasks, and `r`
replicates, the core generation budget is `4 * M * N * r`, before retries or protocol-defined
invalid-response handling.

Compared with Version B, this estimates model heterogeneity and an interaction that distinguishes a
generic information-removal effect from sensitivity to security framing. It also multiplies model
versioning, multiplicity, cost, and interpretive risk. It is a separate behavioral paper-sized
study, not a missing validation check for the current paper.

## Recommendation

Choose **Version A: stop now**. The evidence chain already matches the central estimand: prevalence
of determination, reproducibility of its measurement, and constructive removability. Study 4 would
answer C9, but C9 is not needed to establish that the existing score is non-diagnostic between
requirement following and spontaneous security behaviour.

This recommendation is strengthened by the permanent closure of the Study-3 task-level sample. A
sound Study 4 would need a fresh prospective population and another controlled construction phase;
it is not a cheap final cell that can be appended to the existing analysis. The paper should instead
state the behavioral consequence as the highest-priority future test and preserve the current clean
claim boundary.

No Study-4 protocol is initiated by this memo.

## Post-decision record: behavioural line executed and closed

Added in revision 2. This section reports outcomes; it does not revise the analysis above.

### What was executed

1. **Fresh-sample Study 4 (a Version-B-shaped attempt).** Preregistered on a fresh sample with a
   frozen calibration and yield gate. Stopped at the `transformation_yield` stage with
   `validated_n = 0` of 160 against a preregistered floor of 40 validated pairs. Frozen decision
   `NO-GO`, before any behavioural evaluation. This confirms the memo's cost warning above: the
   fresh constructive pipeline was the binding constraint, not the model budget.
2. **Study 4B, a selected-subset behavioural follow-up.** Because the fresh pipeline did not yield,
   the executed behavioural contrast used the frozen Study-3 demonstrated-separable subset
   (`DS = 47`) in full, `S` versus `S'`, 4 repeats, 376 generations. SecurityPass `+0.5053`
   `[0.3741, 0.6365]`, `p = 4.07e-09`; CapabilityPass `-0.3511` `[-0.4683, -0.2338]`,
   `p = 1.34e-07`; joint `+0.2660` `[0.1051, 0.4268]`. The preregistered +/-5 pp capability
   guardrail **FAILED**. This is an aggregate endpoint contrast on that subset; it opened no
   Study-3 task-level record and performed no subgroup or failure analysis in the confirmatory line.
3. **Study 4C-EX, a post-4B exploratory mechanism experiment.** Four arms on the same 47 tasks
   (`S'`, `S`, `S_controlled`, `S_placebo`), 752 fresh generations, 36/36 pre-generation gates.
   Frozen verdict `MIXED_OR_INCONCLUSIVE`: `Delta_C,mech = -0.0053` `[-0.0939, +0.0833]`,
   `Delta_C,repair = -0.0798` `[-0.1743, +0.0147]`, `Delta_S,preserve = -0.1702` `[-0.2695, -0.0709]`
   (failing its -0.05 noninferiority margin), `Delta_S,generic = -0.0957` `[-0.1580, -0.0335]`. Its
   placebo authoring was negatively conditioned on a prior 20-task exploratory audit of Study-4B
   completions, so it is not outcome-naive independent confirmation.

### What C9 gained and did not gain

C9 was **not** upgraded from unsupported. Version B's stated value was to "directly upgrade C9 from
unsupported to tested for one model and one frozen manipulation". The executed work fell short of
that in two specific ways: the manipulation was applied to a subset selected on Study-3
separability rather than a fresh prospective sample, and the frozen capability-preservation
criterion - a joint condition this memo already flagged as "not a free assumption" - failed. What
the line does establish is that the specification condition matters to one model's behaviour on that
subset, and that the mechanism behind the capability half of the movement is unresolved.

### Line status: CLOSED

The behavioural experiment line is closed. Specifically: no Study 4D; no revision of the
`S_controlled` or `S_placebo` blocks; no added repeats; no task-level or subgroup failure mining; no
new mechanism taxonomy; and no post-hoc hypothesis search over the frozen 752 Study-4C completions.
Any future behavioural work would be a separately preregistered study on a fresh sample with a
manipulation that demonstrably holds capability behaviour constant, and this memo does not initiate
one.

### Net effect on the recommendation

**Version A stands.** The paper's central claim never depended on a behavioural estimate, and the
executed line supplies none. What the line adds is a corroborating behavioural sensitivity on a
selected subset, reported with its guardrail failure attached, plus a strengthened limitations
section. What it removes is the option of promising a forthcoming behavioural answer: the fresh
pipeline did not yield and the mechanism experiment was inconclusive, so the isolated causal
estimand must be stated as future work rather than as work in progress.
