# Instrument Validation Protocol v2 — draft

Status: **FROZEN 2026-08-25.** Supersedes `84ec0d47…`. Any change to this document changes its hash
and voids codings made under it. Consistency check: `scripts/check_protocol_consistency.py`, 37 passed,
0 failed at freezing.

v1 governed Instrument Development Round 1, whose twelve tasks are permanently burned. v2 governs a
**calibration round on a new sample**, drawn from tasks that took no part in developing either
protocol, coded per case by two independent blinded coding runs, to obtain the reliability estimate
v1 could not produce. Whether that estimate is run-level or human-level is a matter of how the runs
are staffed, and is reported as such — see C5.

Round 1's twelve tasks are **not** recoded under v2. Round 1 stands as recorded.

---

## Changes from v1

Each change traces to something Round 1 exposed. Nothing else is altered; Definition D's operative
wording is unchanged.

### C1 — The witness is shown as a complete function

**v1 defect.** The packet showed the benchmark's `vulnerable_code` slot alone. In 5 of 12 tasks that
slot omits the function's `return` statement or its exception handler, which live in `code_after`.
Coder 2 judged two witnesses non-compliant for returning nothing, against a Return field promising a
dictionary — correct reasoning on material that was wrong.

**v2.** The witness is presented as the **assembled function**: `code_before + body + code_after`,
exactly as the runner executes it, with the setup shown separately as part of *S*. Test cases and the
harness remain hidden. The packet builder must construct the witness through the same code path the
runner uses, so the two cannot drift apart again.

### C2 — J1 determination and J3 constructibility are separate constructs

**What Round 1 exposed.** Coder 2 held, coherently, that a setup global's *existence* is not a
sentence obliging its use — so *S* does not determine the safety case — while no functionally
coherent specification could explain that global and still leave the case open. Coder 1 had run these
together. Coder 2's distinction is the better one and is adopted.

**v2** names them separately:

- **Determination** (J1, Definition D unchanged): does *S*, as written, oblige *b* at *i*?
- **Constructibility** (J3): does there *exist* a functionally sufficient specification, under the
  transformation rule, that leaves the safety cases undetermined?

A task may be undetermined-as-written yet non-constructible. That combination is not a contradiction;
it is the signature of a structural carrier, and v1's classification rule could not represent it.

### C3 — The classification rule consults J3

**v1 defect.** §5 routed on J1 alone. Three tasks were computed SEPARABLE while their own coder had
answered that no such specification can exist — including T03, where both coders had named the same
carrying element.

**v2 rule**, applied to a specification *S* and its case sets:

| all capability determined | any safety determined | J3 constructible | class |
|---|---|---|---|
| yes | no | yes | **SEPARABLE** |
| yes | no | no | **STRUCTURALLY CARRIED** — *S* leaves the oracle open but cannot be made coherent while doing so |
| yes | yes | — | **NOT YET BLINDED** |
| no | — | no | **INSEPARABLE** |
| no | — | yes | **OVER-STRIPPED** — the offered *S* is not the best available |

STRUCTURALLY CARRIED is new and is where T03 belongs. It is the class v1 could not express.

### C4 — J3's wording

**v1 defect.** "Can you write a specification *S′* that …" was read as *another, different* one, so
three coders answered "no" while holding an *S* that already had the property.

**v2 wording:**

> Does there **exist** a specification meeting these conditions — the one in front of you counts. If
> the specification you were given already meets them, answer **yes** and name it. Otherwise, either
> give one that does, or name the single element of the signature, the setup code, or the declared
> return type that prevents any from existing.

### C5 — Per-case output from both coding runs, described at the level actually executed

**v1 defect.** κ was pre-specified and turned out to be uncomputable: the first-coder round recorded
per-task gate outcomes, never per-case determinations.

**v2.** Both runs are issued the identical packet and the identical answer template, and both
produce per-case J1. Neither codes specifications it authored. Specification authoring is a **third**
role, performed before either coding run is engaged, and the author does not code.

**Independence is described at the level actually executed.** Where the two codings are produced by
separate sessions or agents rather than by different people, they are reported as **independent
blinded coding runs**, never as independent human coders, and every reliability figure carries that
qualifier. Runs sharing a model or a prompt lineage are not independent in the sense human coders
are, and correlated error cannot be excluded. A human replication, if it becomes available later, is
a **higher grade of validation** and is reported as such rather than merged with the run-level
figure.

### C6 — The tie-break is recorded, not just applied

**v1 defect.** "Undetermined is the default when torn" can only depress the safety rate, and its
usage rate was not recorded, so the blind discrimination result cannot be corrected for it.

**v2.** The tie-break stands, but each case carries a required `confidence` field — `clear` or
`tie_break`. The discrimination check is reported twice: over all cases, and over `clear` cases only.

### C7 — The calibration sample: **90 tasks**

- Drawn from tasks that took **no** part in developing v1 or v2, and never inspected during either.
- Round 1's twelve are excluded by `INSTRUMENT_DEVELOPMENT_ROUND_1.md`.
- Selection frozen by manifest and hash **before** any specification is authored.
- The Round-1 coding run is ineligible.

**Size: exactly 90 tasks**, ~420 case judgements per run. Fixed by the sensitivity analysis in
`round2_sample_size_sensitivity.md`, not chosen afterwards and not derived from any Round-1 rate.

**No augmentation.** 90 is not a minimum. Tasks may not be added after any result is seen, and no
mechanical expansion rule is preregistered here, so none is available later. If the achieved interval
is wider than planned — which the design assumptions in §4 of the sensitivity analysis make quite
possible — that is **reported as the achieved precision**. It is not repaired by sampling more.

**Planning reference value.** The count derives from the worst *unbiased* cell of the grid: a true κ
of 0.60 at a marginal determination rate of 0.80 with no task clustering requires 88 tasks for a 95%
CI half-width of 0.10. 90 is that figure rounded up.

> κ = 0.60 is a **planning reference value only**, chosen because it sits in the middle of the range
> the design must be able to resolve. It is **not** a natural boundary of reliability, and nothing in
> this protocol treats it as one.

**No pass/fail threshold.** Round 2 reports estimates and intervals. It does not classify the
instrument as adequate or inadequate against any κ value, and no such threshold may be introduced
after the estimates are seen. What follows Round 2 is decided from the reported set as a whole (C9),
argued explicitly, and recorded — not read off a cut-point.

**Precision target.** Half-width 0.10 rather than 0.15 for the width itself: an interval of ±0.15
spans nearly a third of the usable range of κ and would leave most of that range compatible with the
data, whichever value came back. ±0.10 is the coarsest width at which the estimate constrains
anything. This is a statement about interval width, not about any threshold the interval might
straddle.

90 of 840 eligible tasks is 10.7%, leaving 750 for the later measurement set, which must not overlap.

### C8 — Pooled κ is descriptive only; inference is cluster-aware

**What the sensitivity analysis observed.** **Under the prespecified simulation DGP of
`round2_sample_size_sensitivity.md`** — a task-level logit shift inducing intra-task correlation, with
equal marginals across runs — Cohen's κ computed from pooled marginals showed a **positive bias** that
grew with clustering: a true κ of 0.60 was recovered as 0.709 at an intra-task correlation of 0.29,
and 0.80 as 0.854. The estimator was unbiased at zero clustering.

This is an observation under one generative model, not a general property of pooled κ. Whether real
disagreement in this corpus behaves that way is unknown, and Round 2 does not assume it.

**v2.** Pooled κ is therefore **a descriptive sensitivity statistic only** and carries no inferential
weight. Primary inference uses a **task-cluster-aware κ** with a **task-level cluster bootstrap CI**.
Reported alongside: the between-task variance of the determination rate and the implied intra-task
correlation, so the discrepancy between the pooled and cluster-aware figures is legible rather than
hidden.

### C9 — Reliability is reported as a preregistered set of statistics

**Why.** A single reliability number invites selection after the fact, and κ in particular is
unstable where marginals are skewed — which §2 of the sensitivity analysis shows is the binding
regime here. Fixing the whole set in advance removes the choice.

Round 2 reports **all** of the following, always together, regardless of what any one of them shows:

| statistic | role |
|---|---|
| **task-cluster-aware Cohen's κ**, CI by task-level cluster bootstrap | primary inferential estimate |
| **pooled Cohen's κ** | descriptive sensitivity statistic only (C8) |
| **raw agreement** on case determination | uncorrected, marginal-free |
| **Gwet's AC1**, same cluster bootstrap | sensitivity to the skewed-marginal instability κ is subject to |
| **quote / evidence concordance** — among cases both runs call determined, whether they cite the same sentence of *S* | agreement on the reasoning, not only the label |
| **tie-break rate** — share of cases marked `tie_break` under C6, per run | how much of the agreement rests on the default |

**AC1 is not interpreted against Cohen κ's verbal thresholds.** Landis–Koch and similar scales were
constructed for κ and do not transfer; AC1 is reported as a number with its interval and compared to
κ only in direction, never mapped onto "substantial", "almost perfect", or any equivalent.

Quote concordance is reported separately from label agreement throughout. Two runs reaching the same
label from different sentences of *S* is weaker evidence that the procedure is reproducible than the
label agreement alone suggests.

---

## Unchanged from v1

Definition D and its two requirements; the definition of *S* as prose + signature + setup/preamble;
the transformation rule; the blinding, including merged and shuffled case lists; classification
computed rather than judged; the fixed order `submit → hash → reveal → compute → save → adjudicate`;
and the rule that no outcome is a failure of the phase.

---

## Open, to settle before freezing

1. *(settled)* **Sample size** is fixed at 90 tasks by C7, over a prespecified grid of marginal
   rates, with no Round-1 rate used as an input.
2. *(settled by C5)* **Role independence** is reported at the level actually executed. Four roles are
   still required — author, two coding runs, adjudicator — but where they are sessions rather than
   people the finding is reported as run-level, not human-level, reliability.
3. *(settled)* **STRUCTURALLY CARRIED and INSEPARABLE are not merged at the label level.** They
   remain distinct underlying classes and their separate proportions are reported in every analysis.
   A presentation may use a prespecified superordinate class aggregating the two, provided the
   aggregation is registered before the data are seen and the component proportions appear alongside
   it. No figure may show only the aggregate.
