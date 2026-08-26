# Does Study 3 earn the term "partial identification"? — formalization

**Status.** Conceptual note; no protocol, no data, no execution. Its job is to formalize the bounds
claimed in the architecture draft and to state exactly what has to hold for "partial identification"
to be the correct term rather than a relabelled trichotomy.

---

## 1. Setup

**Population.** The eligible benchmark frame (the Round-2 frame of 864, or a successor frame frozen
at Study-3 protocol time).

**The latent parameter must be defined without reference to the procedure.** For task *t*, fix the
constraint set **C** once, in the protocol: same signature, same setup, and the target property
stated in Definition-D terms —

> Sep(t) = 1 iff there exists a specification S′ satisfying **C** such that, per Definition D,
> S′ determines the oracle behaviour at every capability case of *t* (functional sufficiency) and
> determines the oracle behaviour at no safety case of *t* (safety-openness).

Sep(t) ∈ {0,1} is well-defined because Definition D is a fixed predicate of a ⟨text, oracle⟩ pair
and the existential quantifier ranges over texts. The population parameter is

> **σ = E[Sep(t)]** — the population separability rate.

Crucially, σ is defined via Definition D directly, **not** as "the rate at which our procedure
succeeds". If it were the latter, the "bounds" would be trivially the data and the term partial
identification would be label abuse. That is the first of the two failure modes this note exists to
exclude.

## 2. The procedure and its outcomes

Study 3's procedure assigns each sampled task one outcome:

- **DS** (demonstrated-separable): a produced candidate passes the J1-based witness check;
- **VO** (verified-obstruction): a structured, quotable obstruction record survives independent
  verification;
- **UR** (unresolved): neither.

Mutual exclusivity of DS and VO is enforced by the procedure's order of operations, and the
contradiction event — a witness passing *and* an obstruction verifying on the same task — is
prespecified as an **instrument-defect signal** that halts interpretation, not a data point.

## 3. Identifying assumptions — stated, not smuggled

- **A-DS (witness soundness).** O(t)=DS ⇒ Sep(t)=1. *A verified witness proves existence.* This is
  an assumption, not a theorem, because the witness check runs through J1 coding, which is fallible
  (Round 2: κ 0.804, not 1.0). It is made conservative by design: DS may be declared only on the
  agreement of both blinded runs' profiles, so its error rate is the *joint* false-profile rate.
- **A-VO (obstruction soundness).** O(t)=VO ⇒ Sep(t)=0. *A verified obstruction proves nonexistence
  under C.* The weaker leg: an obstruction is an argument, not an artifact. It is made conservative
  the same way the whole trichotomy is: any doubt at verification defaults the task to UR.
- **UR carries no assumption whatsoever:** O(t)=UR says Sep(t) ∈ {0,1}.

Under A-DS and A-VO:

> Sep(t) = 1 on {DS}, Sep(t) = 0 on {VO}, Sep(t) ∈ {0,1} on {UR}
>
> ⟹ **σ ∈ [ P(DS), P(DS) + P(UR) ] = [ P(DS), 1 − P(VO) ]**

This interval is the **identified set**, and it is **sharp given the assumptions**: any σ in the
interval is attainable by some assignment of Sep on UR, so no narrower set follows without further
assumptions. That sharpness statement is what distinguishes partial identification from an ad-hoc
interval.

**The error-flow property that makes the design honest:** every failure of nerve — a witness check
one run doubts, an obstruction the verifier is unsure of — flows into UR, and UR only *widens* the
identified set. Hesitation can cost precision; it cannot cost validity. (Errors of *commission*
against A-DS/A-VO are the residual risk, which is why both assumptions are stated and why both are
built conservative.)

## 4. Estimation and inference

The sample analogue gives estimated bounds [P̂(DS), 1 − P̂(VO)] with two distinct widths, reported
separately:

- **identification width** P̂(UR) — a property of the evidence, irreducible by sample size;
- **sampling width** — task-level cluster-bootstrap uncertainty on both endpoints, combined into a
  confidence set for the *parameter* (Imbens–Manski-style CI for partially identified parameters,
  which covers σ, not merely the identified set's endpoints).

## 5. Verdict

**Yes — Study 3 satisfies the term, under three conditions that the eventual protocol must meet,
and it fails the term if any is dropped:**

1. **σ is defined via Definition D and the frozen constraint set C, independent of the procedure**
   (§1). Otherwise the parameter is procedure-relative and the bounds are tautologies.
2. **A-DS and A-VO are printed as the identifying assumptions**, with their conservative
   constructions (§3). Otherwise the bounds rest on hidden soundness claims.
3. **UR is assumption-free** and all hesitation defaults into it (§3). Otherwise the interval can
   narrow dishonestly.

And the distinction to keep visible in the paper: Study 1's measurement-disagreement interval is
**measurement uncertainty about a point-identified parameter** (θ_saf exists as a point; two fallible
runs bracket it); Study 3's interval is **an identification gap** (σ is a point, but the evidence,
even measured perfectly, only confines it to a set). Same square brackets, different epistemology —
the paper names them differently everywhere.

One honest caveat for the limitations section: with fallible measurement inside the witness check,
the clean statement "σ ∈ [P(DS), 1−P(VO)]" holds exactly under A-DS/A-VO and approximately
otherwise; a sensitivity line (bounds under a stipulated misclassification rate for the joint
two-run profile) is cheap to prespecify and closes the gap between "assumed sound" and "shown
robust".
