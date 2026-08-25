# Instrument Validation Protocol v2 — draft

Status: **DRAFT.** Supersedes `84ec0d47…` on freezing. Not yet frozen; no coding under it.

v1 governed Instrument Development Round 1, whose twelve tasks are permanently burned. v2 governs a
**calibration round on a new sample**, drawn from tasks that took no part in developing either
protocol, coded per case by two independent coders, to obtain the inter-rater reliability v1 could
not produce.

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

### C5 — Per-case output from **both** coders

**v1 defect.** κ was pre-specified and turned out to be uncomputable: the first-coder round recorded
per-task gate outcomes, never per-case determinations.

**v2.** Both coders are issued the identical packet and the identical answer template, and both
produce per-case J1. Neither authors the specifications they code. Specification authoring is a
**third** role, performed before either coder is engaged, and the author does not code.

### C6 — The tie-break is recorded, not just applied

**v1 defect.** "Undetermined is the default when torn" can only depress the safety rate, and its
usage rate was not recorded, so the blind discrimination result cannot be corrected for it.

**v2.** The tie-break stands, but each case carries a required `confidence` field — `clear` or
`tie_break`. The discrimination check is reported twice: over all cases, and over `clear` cases only.

### C7 — The calibration sample

- Drawn from tasks that took **no** part in developing v1 or v2, and never inspected during either.
- Round 1's twelve are excluded by `INSTRUMENT_DEVELOPMENT_ROUND_1.md`.
- Selection frozen by manifest and hash **before** any specification is authored.
- Size fixed at freezing from the target precision on κ, not chosen afterwards.
- Coder 2 of Round 1 is ineligible for the calibration round.

---

## Unchanged from v1

Definition D and its two requirements; the definition of *S* as prose + signature + setup/preamble;
the transformation rule; the blinding, including merged and shuffled case lists; classification
computed rather than judged; the fixed order `submit → hash → reveal → compute → save → adjudicate`;
and the rule that no outcome is a failure of the phase.

---

## Open, to settle before freezing

1. **Sample size.** C7 defers it to a precision target for κ. That target has not been chosen, and
   choosing it needs an expected marginal rate for `determined`. Round 1 gives 18/23 and 0/24, but
   Round 1 is burned and its rates cannot be used as an estimate. Either accept a rate assumed from
   outside the corpus, or draw a small throwaway pre-sample that is itself burned.
2. **Third role feasibility.** C5 requires an author, two coders, and an adjudicator — four
   independent parties. If only sessions are available rather than people, the independence claim is
   weaker than the design implies and should be stated as such rather than assumed away.
3. **Whether STRUCTURALLY CARRIED and INSEPARABLE should be reported as one category.** They differ
   in whether functional sufficiency survives, which matters for instrument construction but may not
   matter for the eventual claim.
