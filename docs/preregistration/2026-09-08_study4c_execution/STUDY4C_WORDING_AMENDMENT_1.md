# Study 4C-EX — wording amendment 1 (binding)

**Type:** interpretation-wording amendment to a closed exploratory study. It changes **no** number,
no artifact, no gate, no verdict, and no hash. `STUDY4C_RESULTS.md`
(SHA-256 `3a5f130d7dceab2e36b6f0c5ef1d7d98174132621144bc9f6bb721ee8e3c8b04`) and every frozen
Study-4C data artifact are preserved byte-exact and are **not** rewritten by this amendment.

**Origin:** accepted at Study-4C execution review, 2026-09-08, on the same turn the
`MIXED_OR_INCONCLUSIVE` verdict was accepted and the behavioural experiment line was closed.

## What is narrowed

`STUDY4C_RESULTS.md` section 7 contains, in its third bullet:

> The security loss is the dominant result, and it is largely generic: more than half of it is
> reproduced by the placebo, which contains no security content whatsoever.

That phrasing attributes a share of the total effect to the nonspecific component. That share is
**not identified** by the four-arm design: `Delta_S,preserve` and `Delta_S,generic` are two paired
contrasts against a common reference, and their ratio is not an estimand of this study, has no
interval, and is not protected by any pre-specified criterion.

The same section's closing paragraph on design value contains a second instance:

> A three-arm design would have observed S_controlled security 0.766 vs S 0.936 and attributed it to
> the interface-contract content; the placebo shows that most of the drop is a generic
> added-instruction effect.

Both instances are narrowed by this amendment. The defensible part of that paragraph — that a
three-arm design would have had no way to separate contract-content-specific from nonspecific
added-instruction effects — is retained without the "most of the drop" quantification.

**The binding replacement wording is exactly:**

> The matched placebo demonstrates a substantial nonspecific added-instruction effect on
> SecurityPass, so the S_controlled security loss cannot be interpreted as wholly
> contract-content-specific.

## Binding clauses

1. Every downstream document — synthesis, paper draft, abstract, conclusion, talk — must use the
   replacement wording and must not reproduce the "largely generic" phrasing or the "more than half"
   comparison.
2. **No share, fraction, percentage, or ratio of the SecurityPass effect may be attributed to the
   nonspecific component**, and none may be described with "mostly", "largely", "chiefly", or
   "predominantly".
3. The underlying contrasts remain reportable exactly as frozen: `Delta_S,preserve = -0.1702`
   `[-0.2695, -0.0709]` and `Delta_S,generic = -0.0957` `[-0.1580, -0.0335]`. Readers may compare
   them; the paper may not do the division for them.
4. This amendment does not reopen the study. No Study 4D, no block revision, no added repeats, no
   task-level or subgroup failure mining, no new mechanism taxonomy, and no post-hoc hypothesis
   search over the frozen 752 completions.
5. Everything else in `STUDY4C_RESULTS.md` stands as written, including the permanent
   placebo-authoring disclosure, both recorded gate deviations, and the preserved freeze-abort
   record.
