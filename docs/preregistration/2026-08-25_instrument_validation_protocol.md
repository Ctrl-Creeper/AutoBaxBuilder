# Instrument Validation Protocol — operational definitions and second-coder procedure

Status: **FROZEN 2026-08-25.** Any change to this document changes its hash and voids codings made under it.

Scope: this protocol validates a *judgement procedure*, not a benchmark and not a model. It answers
one question: **can a second coder, without seeing the first coder's conclusions, reproduce the
Determined / Underdetermined / Inseparable classification?** No model is queried; no API cost is
incurred at any point in this phase.

The first coder's judgements are fixed at commit `fcf1120` and are **immutable**. This protocol
produces an independent second set. Disagreements are adjudicated afterwards and recorded; neither
set is edited to match the other.

---

## 1. The primitive: case determination

All four constructs below reduce to one primitive, applied to different sets of cases. Defining them
this way is deliberate: it is what prevents the definitions from resting on one another.

**What *S* is.** *S* is the **complete artefact the implementing model is shown**, not the prose alone:

> *S* ≔ the prose fields (description, context, arguments, return, raise) **+ the setup code**
> **+ the function signature**.

This follows the benchmark's own prompt builder, which emits the prose fields and then
`Setup Code:` verbatim, and presents the signature through `code_before`. Anything in those three
components is available to the implementer and therefore counts as a premise under Definition D.

Fixing this was not cosmetic. The first coder's round left *S* undefined and reasoned over prose
only; §2.1 records what changed when the definition was made explicit.

The unit of coding is **not a specification**. It is the pair

> ⟨ specification *S*, case ⟨input *i*, expected behaviour *b*⟩ ⟩

**Definition D (case determination).** *S* **determines** *b* at *i* iff a competent implementer who
reads only *S*, and who has no access to the test suite, would be obliged by *S* to produce *b* at
*i* — that is, producing anything other than *b* at *i* would put the implementation in
**contradiction with an identifiable sentence of *S***.

Two operational requirements, both mandatory:

1. **Quotation.** A judgement of *determined* is invalid unless the coder quotes the sentence of *S*
   that the alternative behaviour would contradict. No quote ⇒ *undetermined*.
2. **No imported security knowledge.** Determination may pass through **at most one inferential
   step** from the quoted sentence, and that step may not import knowledge from outside *S*. If
   reaching *b* requires a premise such as "an attacker may supply a crafted path", the case is
   **undetermined**.

Requirements 1–2 are inherited verbatim in substance from the already-frozen coding protocol
`eefda969…` (`docs/preregistration/2026-08-06_probe_spec_grounding_protocol.md`), whose classes read:

> **A — 规范逐字(verbatim)**:违反该规则的实现行为,与规范文本中**某一个具体句子构成直接矛盾**。判定时必须能引用那一句。
>
> **B — 规范蕴含(entailed)**:规范没有写出该规则,但从规范中某项陈述**经一步推理**可以得到。……"一步推理"的操作性约束:前提是规范中的单一陈述,结论无需引入规范之外的安全知识。若需要引入,归 C。
>
> **C — 规范沉默(silent)**:规则来自通用安全常识或工程惯例,规范中没有任何陈述可作为前提。

Mapping: **determined ≔ A ∪ B**, **undetermined ≔ C**. This reuse is intentional. That protocol has
already been applied by two independent coders with reported agreement (κ = 0.851 on the A-subtype
round), so Definition D inherits a reliability estimate rather than asserting one.

**Why this is not circular.** D quantifies over *readers of S*, not over implementations. It never
mentions compliance, witnesses, or security. Everything below is D applied to a different case set.

---

## 2. The four constructs

Let *C_func* be the task's capability cases and *C_sec* its safety cases, both taken unmodified from
the benchmark.

**Functional Sufficiency.** *S* is functionally sufficient iff *S* determines *b* at *i* for **every**
⟨*i*,*b*⟩ ∈ *C_func*.

> Grounding note: "intended ordinary functionality" is not left to intuition. It is operationalised as
> the benchmark's own capability suite — the authors' commitment, not ours. A specification that
> leaves a capability case undetermined has been stripped past the functional contract.

**Oracle Underdetermination.** *S* leaves the oracle underdetermined iff *S* determines *b* at *i* for
**no** ⟨*i*,*b*⟩ ∈ *C_sec*.

> This is the definition of Axis 1. It is stated over *S* and the oracle behaviour alone. **It does
> not mention witnesses.** A witness is corroborating evidence for it, never its definition.

**Witness Compliance.** An implementation *W* complies with *S* iff no sentence of *S* is contradicted
by *W*'s behaviour on any input. Judged against *S* alone; the coder judging compliance is not shown
the oracle.

> Witness Compliance is *constructive corroboration* of Oracle Underdetermination: if *W* complies
> with *S*, passes *C_func*, and fails *C_sec*, then at least one *S*-compliant behaviour differs from
> the oracle's expectation, which is inconsistent with *S* determining that case. It strengthens the
> claim; it cannot substitute for it.

**Inseparability.** A task is **inseparable under this protocol** iff every *S* obtainable under the
transformation rule (§3) that is functionally sufficient also determines at least one case in *C_sec*.

> Because "every *S*" is not decidable by inspection, an inseparability claim is admissible only in
> **obstruction form**, and is falsifiable:
>
> - the coder must **name the carrying element** — a signature parameter, a global named in the
>   setup, or the declared return type — and
> - must argue that any *S* explaining that element's purpose thereby determines a case in *C_sec*.
>
> A second coder defeats the claim by **exhibiting** a functionally sufficient *S* that leaves *C_sec*
> undetermined. This mirrors Separability, which is established by exhibiting a witness. Both
> classifications therefore carry a constructive obligation, and neither is a residual bucket.
>
> The claim is always **relative to this protocol's transformation rule**. No assertion is made that a
> task is inseparable in principle.

### 2.1 Three structural carriers of the obligation

Making *S* explicit enumerates where a security obligation can live. Only the first is removable
under §3, which is what gives Inseparability its content:

| carrier | removable? | first-coder count over the 12 tasks |
|---|---|---|
| **Prose** — a clause in description / context / arguments / return / raise | yes | 10 of 12 carried it outside `security_policy` |
| **Signature** — a required parameter whose only role is the security decision | no | 2 (`is_superuser`, `current_user_id`) |
| **Setup** — a global whose *name or value* states the rule | no | 6 (`ALLOWED_CDN_DOMAINS`, `APPROVED_API_DOMAINS`, `ALLOWED_ENDPOINTS`, `ALLOWED_DOMAINS`, `ALLOWED_REDIRECT_DOMAINS`, `ALLOWED_FIELDS`, `TRUSTED_DEVICE_SIGNATURES`) |

The setup carrier was missed in the first-coder round and is recorded here as a finding of this
phase, not as a correction folded into the prior result. Its consequence is stated in §7.5.

The generalisation this supports, and which the second coder's J3 is designed to test independently:

> A security obligation may be carried **propositionally** in the task prose, or **structurally** in
> the executable interface the benchmark supplies — its parameters and its preamble. Only the
> propositional carrier can be ablated. Where the obligation is structural, a
> security-underdetermined specification does not exist to be constructed, so an
> ablation-based experimental design is not merely expensive but ill-posed for that task.

---

## 3. Frozen transformation rule

A candidate *S* is obtained from the original `task_description` by rewriting its prose fields only.
**Immutable:** the function signature, the `setup` code, every capability case, every safety case, and
the ground-truth implementations. Any change to these voids the task.

---

## 4. What Axis 2 is, and why it is measured differently

**Axis 2 (security framing).** *S* is security-framed iff it names a threat, an attacker, a
vulnerability class, or a security property.

Axis 2 admits automated lexical screening. **Axis 1 does not, and no lexicon will be extended to make
it.** The first coder's lexical screen failed in three separate ways (`\blimit\b` missing "limits";
no `vulnerab\w*`; no "authorized / permitted / approved / diverge"), but patching those terms is the
wrong repair, because the decisive counterexample carries **no security vocabulary at all**:

> SeCodePLT idx=434 — `return`: *"return the data as a dictionary **if the signature is verified
> successfully; otherwise, return None**"*; safety case: wrong signature → `None`.

The methodological consequence is frozen here:

> **Security framing can be lexically approximated; oracle determination cannot. Axis 1 is
> oracle-relative and must be coded over ⟨specification, oracle behaviour⟩ pairs.**

---

## 5. Second-coder procedure

**Materials.** All **12** tasks, presented uniformly, in an order fixed by a seed recorded in the
packet. Every task carries a candidate *S*, including the two the first coder judged inseparable —
for those, *S* is the first coder's maximally-stripped attempt. The packet is generated by
`scripts/build_coder2_packet.py`.

**Withheld from the second coder.** The first coder's classifications, gate outcomes, removal table,
stratum labels, the words "separable" and "inseparable", the original unmodified `task_description`,
the `security_policy` field, the CWE identifier, and commit `fcf1120`.

**Case labels are withheld.** For each task, *C_func* and *C_sec* are **merged and shuffled** into one
unlabelled case list. The coder is not told which cases are security cases, and is not told that any
are. This makes the capability cases an internal control: an instrument that works should show the
coder marking capability cases *determined* and safety cases *undetermined* without knowing which is
which.

**Three independent judgements per task**, in this order, with no back-editing once submitted:

| # | Judgement | Shown | Output |
|---|---|---|---|
| J1 | Case determination | *S* + the shuffled case list | per case: determined / undetermined + the **quoted sentence** when determined |
| J2 | Witness compliance | *S* + witness source | complies / does not comply + the contradicted sentence when not |
| J3 | Obstruction | *S* + signature + setup globals | can a functionally sufficient *S′* be written that leaves the remaining cases undetermined? yes + the *S′*, or no + the named carrying element |

J1 precedes J2 so that seeing the witness cannot influence determination judgements. J3 is asked for
**every** task, not only the disputed ones, so that its being asked carries no information.

**Classification is computed, never judged.** The coder never assigns a class. From J1–J3:

- all *C_func* determined **and** no *C_sec* determined **and** witness complies → **SEPARABLE**
- all *C_func* determined **and** ≥1 *C_sec* determined → **NOT YET BLINDED** (transformation incomplete)
- ≥1 *C_func* undetermined **and** J3 = no → **INSEPARABLE**
- ≥1 *C_func* undetermined **and** J3 = yes → **FIRST CODER OVER-STRIPPED** (*S′* supersedes)

---

## 6. Pre-specified analysis

Reported regardless of outcome:

1. Cohen's κ on case determination, over all ⟨task, case⟩ pairs pooled — the primary reliability
   figure, since J1 is the primitive everything else reduces to.
2. Cohen's κ on witness compliance and on the obstruction judgement, per task.
3. Agreement on the **computed** classification, with the full 12-row disagreement table.
4. **Quote concordance:** among cases both coders call determined, how often they quote the same
   sentence. Two coders reaching the same class from different sentences is weaker agreement than the
   κ implies, and is reported separately.
5. Discrimination: within each task, whether *C_sec* cases were called undetermined at a higher rate
   than *C_func* cases, coder-blind to the labels.

**No threshold is set as a pass mark, and no outcome is a failure of the study.** This is an
instrument-development set. If κ is low, the definitions are ambiguous, and exposing that is the
purpose of the phase.

**Adjudication.** Every disagreement is resolved by a third party who sees both codings and both
quotes, and the resolution is recorded with its reason. Adjudication may not silently rewrite a
definition: any definitional change produces **v2 of this protocol**, separately frozen, and **both**
coders recode the 12 tasks under v2.

**Stopping rule.** The task set is **not** expanded beyond 12 until κ on J1 and the full disagreement
table have been reported. The 12 tasks are an instrument-development set and are excluded from any
later measurement or experimental set.

---

## 7. Known limitations of this phase, recorded in advance

1. **The mechanical gates in the first-coder round were non-binding.** SeCodePLT's construction
   invariant guarantees that its `vulnerable_code` passes capability and fails safety for every task,
   and the first coder's selection filter required exactly that. So "gate 2 passed 10/10" carried no
   independent information. The binding evidence was, and remains, human judgement. This protocol
   exists because of that.
2. **The witness bodies are the benchmark's own `vulnerable_code`.** This defends against the charge
   that the witness is a strawman, but it also means the witnesses are not independent of the
   benchmark's own notion of the defect.
3. **The first coder was non-blind** — they authored the specifications they then judged. The second
   coder is blind to the first coder's output but is not blind to the fact that *S* was constructed
   for a purpose.
4. **n = 12.** This phase estimates agreement, not prevalence. No claim about how common
   separability is in SeCodePLT may be drawn from these 12 tasks.
5. **The first coder's separability calls are provisional under the corrected definition of *S*.**
   They were made over prose alone. Six of the ten tasks recorded as separable at `fcf1120` have a
   setup global that names the rule, so at most four of the twelve are separable on the first
   coder's own reasoning once §1's definition of *S* is applied. That record is deliberately **not**
   edited: the second coder codes against this protocol, and the two sets are compared as they
   stand. The gap between the `fcf1120` classification and the second coder's is therefore expected,
   and its size is itself a measurement of how much the undefined *S* was doing.
