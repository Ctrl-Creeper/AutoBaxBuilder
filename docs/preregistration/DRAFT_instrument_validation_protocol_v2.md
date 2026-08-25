# Instrument Validation Protocol v2 — draft

Status: **DRAFT.** Supersedes `84ec0d47…` on freezing. Not yet frozen; no coding under it.

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

**Size and its basis.** 90 tasks, ~420 case judgements per run. Fixed by the sensitivity analysis in
`round2_sample_size_sensitivity.md`, not chosen afterwards and not derived from any Round-1 rate. The
worst *unbiased* cell — true κ = 0.60, marginal determination rate 0.80, no task clustering — requires
88 tasks for a 95% CI half-width of 0.10 on κ. 90 is that figure rounded up.

Half-width 0.10 rather than 0.15 because the round has to decide whether κ clears a threshold: at
0.15, an observed κ̂ of 0.75 yields [0.60, 0.90], which touches the threshold and settles nothing; at
0.10 it yields [0.65, 0.85].

90 of 840 eligible tasks is 10.7%, leaving 750 for the later measurement set, which must not overlap.

### C8 — κ must be reported clustering-corrected

**What the sensitivity analysis exposed.** Cohen's κ computed from pooled marginals is **upward
biased** when the determination rate varies across tasks, because task heterogeneity depresses the
chance-agreement term. Simulated: a true κ of 0.60 reads as 0.709 at an intra-task correlation of
0.29; 0.80 reads as 0.854. The bias grows with clustering and is present at every marginal rate.

**v2.** The headline reliability figure is **not** the pooled κ. Round 2 reports:

1. pooled κ, labelled as an upper bound;
2. the between-task variance of the determination rate, and the implied intra-task correlation;
3. a clustering-corrected κ — task-stratified, or with a task random effect — as the primary figure;
4. the CI by cluster bootstrap over tasks, not over cases.

Had this gone unchecked, Round 2 would have reported a κ that looked substantial while the true value
sat below the threshold.

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
