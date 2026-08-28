# Study 3 — estimand–estimator audit for the three-layer inference

**Status.** Statistical audit required before protocol freeze, per the CR-1 ruling message. No S′
authored, no formal sample drawn, no coding. Evidence: `study3_inference_audit_sim.py` with
`study3_inference_audit_results.json` (R=2000 replications per scenario, B=400 bootstrap, seed
20260828; design mirrored: SRSWOR N=90 from a finite frame, stochastic measured eligibility,
stochastic DS/VO/UR outcomes with A-DS/A-VO holding except in the negative fixture).

## The three layers, and what estimates what

| layer | target | estimator | audit verdict |
|---|---|---|---|
| **L0 identification (primary, fixed by ruling)** | the measured-eligible sample's own separable share | descriptive **[P̂(DS), 1−P̂(VO)]** | **exact**: containment 1.0000 in every assumption-holding scenario (interior, VO-boundary, low-yield m̄=19, high-DS). It is a finite-sample logical consequence of A-DS/A-VO, not an asymptotic statement — and it is assumption-bearing, not tautological: the negative fixture (50% false witnesses on a mostly-inseparable frame) drives containment to **0.0000** |
| **L1 sampling** | π_DS, π_VO — the eligible-subpopulation outcome rates under the same measurement process | **per-endpoint Clopper–Pearson conditional on m** — ADOPTED | coverage ≥ 0.968 in every scenario, **1.000 at the π_VO = 0 boundary**, holds at m̄ = 19; conservative, never below nominal |
| | | percentile bootstrap over the 90 drawn tasks — **REJECTED** | π_VO coverage 0.933–0.940 < 0.95 in three of four scenarios (small-count undercoverage) |
| **L2 measurement** | sensitivity of L0's endpoints to the two-run rule | prespecified descriptive contrasts: DS under both-runs (the definition) vs either-run profile; eligibility under both-agree (the rule) vs either-agree | reported as separate rows, never pooled into L0/L1 |

## Imbens–Manski / combined intervals — not adopted

The audited IM interval for σ (bootstrap endpoint SEs, standard IM critical value) covered σ at
0.995–1.000 in every assumption-holding scenario. That is not validation; it is the diagnosis:

- IM answers point-parameter inference for a partially identified σ. Under this design the
  identified set's width P(UR) dominates sampling noise, so the IM interval degenerates to
  "the descriptive interval plus a negligible margin" — over-covering trivially while adding no
  information beyond L0 + L1.
- Reporting it would manufacture exactly the **single merged headline interval** the ruling
  prohibits, inviting the misreading of identification width as statistical uncertainty.
- The correspondence demanded by the ruling — a method matched to "random baseline sample +
  measured eligibility + DS/VO/UR" — is met by the L0/L1/L2 decomposition itself, not by a
  composite.

**Ruling implemented: no combined interval of any kind is reported. The headline is L0's
descriptive interval; L1 gives two separate Clopper–Pearson CIs (one per endpoint); L2 gives the
measurement-sensitivity contrasts. One table, three named layers, no merging.**

## Notes carried into the protocol at freeze

1. L1's population targets are **procedure-inclusive**: π_DS and π_VO are rates of the
   ⟨sampling, baseline screen, constructive procedure⟩ pipeline over the eligible subpopulation,
   stated as such, superscripted to the frozen eligibility rule. No superpopulation language is
   needed (the frame is finite and frozen; SRSWOR fpc is ignored, which is conservative).
2. m (eligible yield) is random and reported as a result, not a target; CR-1 bars any reaction
   to it.
3. If m = 0, L0 is empty and every layer reports "no eligible tasks" — prespecified, no
   improvisation.
4. The negative fixture stays in the frozen sim as the standing demonstration that L0 is
   assumption-bearing; A-DS/A-VO remain printed identifying assumptions with their conservative
   constructions (both-runs witness profile; decidable-certificates-only VO).
