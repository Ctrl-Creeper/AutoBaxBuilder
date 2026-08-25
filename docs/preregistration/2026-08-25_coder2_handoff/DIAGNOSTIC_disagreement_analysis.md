# Diagnostic disagreement analysis — Instrument Development Round 1

**Diagnostic only. Nothing here is adjudicated.** No disagreement is resolved, no coding is revised,
and neither coder is recorded as correct. The purpose is to identify the *mechanism* behind each of
the six classification disagreements, because those mechanisms are the input to Protocol v2.

Inputs: coder 1 at `fcf1120`, coder 2 at `536d8824…` (frozen, `dde8fcc`), scored under `84ec0d47`.

---

## 1. The headline is not 6/12

Classification agreement was 6/12. Sorting the six disagreements by mechanism:

| task | idx | coder 1 | coder 2 | mechanism |
|---|---|---|---|---|
| T07 | 1072 | INSEPARABLE | UNRESOLVED | witness-fragment defect |
| T08 | 1067 | SEPARABLE | UNRESOLVED | witness-fragment defect |
| T01 | 666 | SEPARABLE | INSEPARABLE | coder 1 never judged functional sufficiency |
| T04 | 643 | SEPARABLE | INSEPARABLE | coder 1 never judged functional sufficiency |
| T12 | 434 | SEPARABLE | INSEPARABLE | coder 1 never judged functional sufficiency |
| T03 | 1364 | INSEPARABLE | SEPARABLE | J3 / computation-rule interaction |

**None of the six is a substantive disagreement about the phenomenon.** Two are a defect in the
materials, three are an asymmetry in what the two rounds actually judged, and one is a defect in the
protocol's own classification rule. This is a claim about mechanism, not about who was right; the
question of correctness is left open for the calibration round.

### The asymmetry behind T01, T04, T12

Coder 1's Gate 1 asked whether the benchmark's `patched_code` still passed the capability suite.
That is trivially true for every task, because the transformation rule forbids touching the tests.
Coder 1 therefore **never made a functional-sufficiency judgement in the sense of Definition D** —
that definition was written afterwards, for the protocol.

Coder 2 did make it, and found capability cases undetermined in these three. Coder 1 has no
corresponding judgement to disagree with. The rows differ because one round judged something the
other did not.

### T03 is defect 2, not a reversal

Both coders named the **same** carrying element. Coder 1: `current_user_id` is a required parameter
whose only role is the authorisation decision. Coder 2, J3, unprompted:

> the `current_user_id` parameter … current_user_id is passed but has no stated effect, and any S'
> that says why the caller supplies it must state a permission rule, which settles cases 1–3 as False.

They agree on the mechanism and on the element. The classifications diverge only because §5's rule
routes on J1 alone: all capability cases determined and no safety case determined ⇒ SEPARABLE, with
J3 never consulted. So the rule produced SEPARABLE for a task whose own coder had just said no
coherent specification of this shape can exist.

---

## 2. The structural-carrier claim was independently reproduced

The sealed provenance note (`fcf1120` → `84ec0d47`) claimed three carriers, two of them irremovable:
prose, signature parameters, and setup globals. Coder 2 never saw that note, was never told the
study's direction, and was never told that setup code could carry an obligation.

Their J3 answers name the carrying element on all four tasks where a structural carrier was claimed:

| task | coder 2's named carrier | coder 2's reason (verbatim, abridged) |
|---|---|---|
| T01 / 666 | setup global `ALLOWED_CDN_DOMAINS` | "Any S' that says what that allow-list is for must state that a cdn_base outside it is refused" |
| T04 / 643 | setup global `ALLOWED_DOMAINS` | "…must say that a next parameter pointing outside it is refused" |
| T12 / 434 | parameter `crypto_signature` **+** setup global `TRUSTED_DEVICE_SIGNATURES` | "…must state what happens when the two disagree" |
| T03 / 1364 | parameter `current_user_id` | "…must state a permission rule" |

**This is reproduction of the mechanism, not of the classification.** It is the strongest result of
the round, and it is why the round is worth keeping despite its defects.

### Coder 2's refinement, which is better than the original formulation

Coder 2 held two things at once that the first coder had run together:

> "no prose sentence mentions validating cdn_base, and 'Raise: None' points the other way, so
> ValueError is not obliged; **the global's mere existence is not a sentence requiring its use**"
> — and yet no coherent `S'` can explain the global without settling the case.

So *S* does **not** determine the safety behaviour, while *no functionally coherent S* could leave it
open. Those are different properties, and the first coder conflated them. Separating them is adopted
in v2 as two distinct constructs rather than one.

---

## 3. The blind discrimination check

With capability and safety cases merged, shuffled and unlabelled, and with the coder never told the
distinction exists:

```
capability cases called determined   18 of 23   0.78 pooled
safety     cases called determined    0 of 24   0.00 pooled
tasks where safety < capability       10 of 12  (the other two are ties at zero)
```

(The scoring script prints 0.79 for capability; that is the mean of per-task rates. The pooled rate
over all 47 cases is 0.78. Both are reported so neither is mistaken for the other.)

Read with two cautions, both left unresolved:

- The instruction "undetermined is the default when you are torn" can only push the safety figure
  down. That it did not also flatten the capability figure argues against a blanket bias, but the
  tie-break's usage rate was not recorded and cannot be recovered. v2 records it.
- Twenty-four safety cases across twelve tasks is a small denominator. A clean separation here is
  encouraging, not established.

---

## 4. What this round cannot support

- **No inter-rater reliability.** κ needs per-case determinations from both coders; the first round
  produced per-task gate outcomes only.
- **No prevalence claim.** n = 12, selected for a purpose, and now permanently excluded from any
  measurement set.
- **No claim that either coder was correct** on any of the six disagreements.
- **J2 is unsound** for T07 and T08 and unestablished for T03, T05, T12.
