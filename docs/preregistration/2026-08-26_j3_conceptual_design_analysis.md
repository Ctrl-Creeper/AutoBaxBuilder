# Why J3 was constant — conceptual design analysis and options

**Status.** Analysis only. Zero API calls, zero new coding, zero protocol edits. Every empirical
statement below reads a frozen artifact; every design option is a proposal awaiting a decision, and
none is executed. Companion to `2026-08-26_round2_interpretation_memo.md`.

The question this document must answer, per the checkpoint instruction: is J3's failure a repairable
defect of an annotation item, or was Constructibility never the same class of measurement problem as
Determination in the first place? The instruction's constraint is honoured throughout: **no
explanation or option is preferred because it preserves the taxonomy.**

---

## Part I — Three explanations for the constant, compared

### E-a. Sampling / support: the corpus is saturated — every task really is constructible

If nearly all SeCodePLT tasks admit a blinded specification, J3 = true on 90/90 is the *correct*
answer and the problem is only that the sample gives no false-branch support.

**Against it, from frozen artifacts:**
- The writer role, which actually *attempted* construction on every task, declared structured
  obstructions on 37/90 (25 `F1_LIST_COUPLING`, 12 `F3_PREAMBLE_CARRIER`). Not ground truth — but a
  competent attempt hitting a wall on 41% of tasks is incompatible with "obviously saturated".
- The coders' own J1 corroborates the wall (memo §4): on writer-failure tasks, 32/37 derived to
  NOT_YET_BLINDED or OVER_STRIPPED; on no-failure tasks, 37/53 derived to SEPARABLE in both runs.
- Round 1's twelve development tasks already contained coder-asserted INSEPARABLE outcomes.

**Verdict:** cannot be excluded as a *contributor* (true constructibility prevalence may genuinely
be high), but it cannot be the whole account, and — decisive for design — even if it were true, a
measurement that cannot exercise its false branch on any realistic corpus is not validated by
agreeing with saturation. E-a alone would still leave J3 unvalidatable by this design.

### E-b. Writer conditioning: the pipeline delivers only pro-existence evidence to the judge

The pipeline is:

```
original task ──▶ writer must produce a candidate S′ for every task
                  (INSTRUCTIONS §4: failure "is never a reason to drop a task";
                   "still produce your best candidate")
                        │
                        ├── candidate S′ ───────────────▶ shown to coder
                        └── failure declaration (F1–F5) ─▶ withheld from coder (blinding, correct)
                        
coder ──▶ J3: "does there exist a specification meeting these conditions —
              the one in front of you counts"
```

Three structural facts:

1. **P(coder holds a candidate) = 1 regardless of true constructibility.** The writer had a failure
   channel but no *abstention* channel: even a declared-impossible task ships its best candidate.
2. **The information flow is asymmetric by construction.** The writer's work product splits into
   pro-existence evidence (the candidate) and pro-nonexistence evidence (the failure declaration).
   The blinding boundary — correctly drawn for J1's sake — transmits the first and withholds the
   second. The coder judges an existence claim holding only the half of the record that supports it.
3. **"The one in front of you counts" (C4) imports the writer's success as prima facie evidence.**
   This wording was a correct fix to the v1 defect (three coders answering "no" while holding a
   conforming S). Its cost is now visible: it makes the candidate itself a proposed witness, so
   assent requires only *not spotting a defect* in it, while refusal requires an argument.

Is this circularity? Strictly, conditioning rather than circularity: the coder is not asked "did
the writer succeed", and a coder could in principle answer false while holding a candidate. But the
design makes the existential judgement *conditional on a forced construction attempt whose failure
record is invisible* — so the coder channel could only ever recover nonexistence through the coder's
own unaided obstruction proof. Which E-c shows was nearly impossible.

**Verdict:** established from the frozen texts and the pipeline structure. E-b guarantees a strong
bias toward `true` independent of the corpus.

### E-c. Formulation: the binary J3 item is epistemically asymmetric and its false branch is incomplete

Two defects, both decidable by reading the frozen C4 wording — no data needed:

1. **Asymmetric burden.** `exists = true` is witnessable at zero cost: point at the candidate, or
   mentally delete an offending sentence. `exists = false` is a **universal negative over an
   unbounded space of texts** — and C4 demands, as the only admissible proof, "the single element of
   the signature, the setup code, or the declared return type that prevents any from existing". True
   is free; false requires an obstruction proof. Any uncertainty resolves to true.

2. **The false branch cannot express the most common obstruction.** C4 admits only *structural*
   obstructions (signature / setup / return type). The writer's modal failure — `F1_LIST_COUPLING`,
   25 of 37 declarations: *every phrasing sufficient for the capability cases also settles the
   safety case* — is a **prose-level coupling obstruction with no corresponding J3 = false path.**
   A coder convinced of exactly that coupling has no legal way to answer false. The instrument's
   false branch was incomplete relative to the phenomenon's known failure taxonomy — a taxonomy the
   same protocol suite had already written down, in the writer's INSTRUCTIONS §4, before either
   coding run started.

3. **Coherence coupling with J1 (corollary).** Both runs' J1 located every one of their 28
   disagreement quotes — indeed every determination quote — in prose; neither run ever attributed a
   determination to signature or setup. A coder whose own J1 evidence never touches a structural
   carrier cannot coherently name one as blocking all possible specifications. Given each run's J1
   pattern and C4's wording, **J3 = true on every task was very nearly entailed.** J3 as executed
   was not an independent measurement; it was approximately a function of J1's carrier profile.

**Verdict:** established. E-c makes the constant close to inevitable even on a corpus rich in
inseparable tasks.

### Joint answer to the checkpoint question

The constant is overdetermined by E-b and E-c jointly; E-a is undecided and immaterial to the design
conclusion. And the deeper classification the instruction asked about is real:

> **J1 and J3 are different classes of measurement problem.** J1 is a decidable predicate of a fixed,
> given text: it is confirmed by a quotation and refuted by the absence of one, which is why
> annotation methodology — blinded coders, agreement statistics — fits it, and why it validated.
> J3 is an **existential claim over an unbounded space of possible texts**: verifiable only by
> exhibiting a witness, refutable only by proving an obstruction. Asking a blind annotator to check
> a box for such a claim was a category error, not a wording bug. No rewording of a binary item
> removes the asymmetry between "here is a witness" and "no witness can exist".

The practical corollary: constructibility should be *demonstrated or obstructed*, not *annotated* —
which frames the options.

---

## Part II — Design options (none executed)

### Option 1 — Keep J3 as an annotation; redesign its validation independently

Fix the two E-c defects in a v3 item (add a coupling clause to the false branch; judge without a
candidate in hand to remove E-b), and buy discriminative support with **seeded criterion items**:
tasks constructed so that the obligation is provably signature- or setup-carried (false by
construction) mixed into a fresh sample.

- **Estimand.** P(∃ functionally sufficient, safety-open S′) over corpus tasks, as judged by blinded
  annotators; criterion validity estimated on seeds.
- **New data.** A fresh task sample from the untouched pool + constructed seed items + two new
  blinded coding runs.
- **LLM/API.** Coding-run sessions (conversation cost); no eval API.
- **Contamination.** Burns a fresh slice of the remaining pool; seeds are synthetic and burn
  nothing. The 90 stay development-only, per the memo.
- **Likeliest reviewer attack.** (i) Seeds are strawmen — reliability on constructed negatives does
  not transfer to natural items; (ii) the item is still a universal negative judged by inspection:
  an annotator who *fails to find* an S′ has proven nothing; (iii) without a candidate in hand the
  judgement becomes speculation about an unattempted construction. These attacks are, in substance,
  Part I restated — the option patches E-b and half of E-c but leaves the category error intact.
- **Contribution to the paper.** Preserves the taxonomy in its original form; weakest epistemic
  footing of the three.

### Option 2 — Replace the annotation with a constructive-witness / obstruction procedure

Constructibility stops being a checkbox and becomes a **two-sided procedure**, both sides reducing
to already-validated machinery:

- **Positive side (witness).** A task is *separable-as-demonstrated* iff a produced candidate S′
  passes the J1-based check: blinded runs code S′ under Definition D and find all capability cases
  determined and no safety case determined. The check *is* J1 — the primitive Round 2 just showed
  reproducible (cluster-aware κ 0.804). Round 2 in fact already ran this check without naming it:
  the ~0.37 safety-determination rate under S′ is per-case evidence, with known reliability, that
  many candidates fail openness.
- **Negative side (obstruction).** A task is *obstructed-as-argued* iff the construction attempt
  terminates in a structured obstruction record — the existing F1–F5 taxonomy, now **including
  coupling (F1)** as a first-class obstruction — whose every claim is quotable and is verified by an
  independent role the way J1 quotes are checked (e.g. an F1 record must exhibit the capability case
  and the sentence that settles it and show that sentence settling the safety case).
- **Estimand.** A pair of bounds, honest about procedure-relativity: the demonstrated-separable rate
  (lower bound on separability) and the verified-obstruction rate (lower bound on inseparability),
  with an explicit unresolved band between them. INSEPARABLE and STRUCTURALLY_CARRIED become
  *procedurally earned* labels, never annotator opinions.
- **New data.** Fresh tasks; writer run(s); two blinded J1 runs over the candidates; an obstruction
  verification role. Same operational shape as Round 2 — every frozen tool (validators, packet
  builder, alignment, scoring) reuses.
- **LLM/API.** Writer + coder sessions; no eval API.
- **Contamination.** Fresh pool slice. The 90 burnt tasks become exactly what the memo permits:
  development evidence for the procedure's mechanics (the cross-tab in memo §4 is, in effect, its
  pilot).
- **Likeliest reviewer attack.** (i) "Your lower bound measures your writer's skill, not the task"
  — true and answered by reporting it *as* a bound, optionally tightened with a second independent
  writer; (ii) "obstruction verification is itself a judgement" — blunted because every obstruction
  claim is quotable and checked the same way J1 was, inheriting its reliability argument;
  (iii) the unresolved band may be wide — a reporting cost, not a validity flaw.
- **Contribution to the paper.** Strongest: the whole taxonomy becomes derivable from Definition D
  plus procedures, which is already the paper's thesis; the Round-2 reliability result powers every
  branch; and the witnesses it produces are literally the U-variant specifications Study 3
  (Manipulate) needs, so no work is stranded even if the taxonomy is later demoted.

### Option 3 — Contract the main line to Determination; constructibility becomes secondary/exploratory

The paper's validated spine becomes: Definition D → J1 reliability → oracle-underdetermination
prevalence → the manipulation study. Constructibility is never claimed corpus-wide; it is
demonstrated **per item, by construction**, only for the tasks Study 3 actually uses (each usable
U-variant is its own witness, verified behaviourally when the manipulation runs), and Round 2's
constructibility-adjacent observations are reported as exploratory description.

- **Estimand.** Determination / underdetermination rates with the validated instrument; the
  manipulation effect. No constructibility estimand.
- **New data.** None for the instrument line; Study 3's eval runs as already planned.
- **LLM/API.** Only Study 3's already-budgeted eval spend.
- **Contamination.** None new.
- **Likeliest reviewer attack.** (i) "The 2×2 design's D-axis presupposes constructibility you never
  validated" — partially answered per-item, but the *corpus-level* claim quietly disappears;
  (ii) "a taxonomy was promised and two of its five classes were never measured" — must be conceded
  openly; (iii) the paper's scope shrinks from "a taxonomy of leakage" to "a validated primitive and
  one manipulation".
- **Contribution to the paper.** Smallest risk, cleanest claims, real loss of the taxonomy headline.

*(Options 2 and 3 converge operationally: Option 3's per-item demonstrations are Option 2's positive
side run only where Study 3 needs it. Option 2 ⊃ Option 3's constructibility content.)*

---

## Recommendation (not executed)

**Option 2**, on the strength of Part I rather than of the taxonomy: the analysis concluded that
existence claims are demonstrated or obstructed, not annotated, and Option 2 is the only option
whose measurement class matches that conclusion. Secondary reasons, each independent of taxonomy
preservation: it is the sole option giving the F1 coupling obstruction — empirically the dominant
one — a first-class expression; it reuses the validated J1 primitive and every frozen Round-2 tool;
and its positive-side artifacts are Study 3's inputs, so the work is not stranded under any later
scope decision.

If the decision instead favours epistemic minimalism, **Option 3 is fully defensible and loses no
option value** — Option 2 can be mounted later, unchanged, because the 90-task sample restriction
(memo §5.2) binds either way. Option 1 is not recommended: it repairs the wording while keeping the
category error.

Awaiting decision. Nothing further is executed.
