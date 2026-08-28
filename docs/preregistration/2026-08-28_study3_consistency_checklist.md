# Study 3 protocol — consistency checklist (to be run mechanically at freeze)

Each item becomes a check in a freeze-time script, in the style of the Study-1 protocol checker
(negation-aware where a banned phrase legitimately appears inside a prohibition).

## Estimand and identification
- [ ] σ defined via Definition D + constraint set C, independent of the procedure; the words
      "procedure-relative" appear only as a disclaimer about bounds, never in σ's definition.
- [ ] Identified set stated as [P(DS), 1−P(VO)] with A-DS and A-VO printed as identifying
      assumptions; sharpness sentence present; UR carries no assumption.
- [ ] The three uncertainty layers (identification / sampling / measurement) named apart;
      Study-1's [both, either] never described as an identification interval, and vice versa.

## Outcomes
- [ ] DS requires both blinded runs' profiles: all capability determined AND no safety determined.
- [ ] VO restricted to the enumerated certificate types; a "writer failure ⇒ VO" path does not
      exist anywhere in the text; coupling claims route to UR with descriptive reporting.
- [ ] DS∧VO defined as instrument-defect halt.
- [ ] No occurrence of Round-2 J3 TRUE/FALSE as an outcome; J3 named only as
      instrument-development evidence (negation-aware check).

## Selection and conditioning
- [ ] Exclusion list = 90 ∪ reserve-10 ∪ IDR1-12 ∪ feasibility tasks, built mechanically from
      frozen manifests, frozen with the protocol.
- [ ] Eligibility rule (both-runs ≥1 safety case determined at baseline) stated before any
      fresh-task outcome exists; no Study-1 case-level outcome in any selection/eligibility path.
- [ ] CR-1 resolved by explicit user ruling recorded in the protocol; the ruling's option and its
      rationale quoted; no θ value appears except as that ruling permits.
- [ ] Fresh-draw seed derived from this protocol's own hash; single draw, no reroll.

## Constraints C
- [ ] Immutable set enumerated: setup, function name, closing instruction, all cases, field schema.
- [ ] Editable set enumerated: five prose fields + security_policy (removable).
- [ ] Parameter-mention preservation stated and mechanically checkable.
- [ ] Capability preservation and safety underdetermination judged only by blinded J1 evidence;
      the validator's scope excludes semantic adequacy.

## Data flow and blinding
- [ ] Writer sees labels (estimand-set boundary); coders never see labels, derivation status, or
      baseline existence.
- [ ] Baseline and witness stages use disjoint fresh sessions; stated as a hard rule.
- [ ] Candidate S′ and writer declarations both preserved regardless of outcome.
- [ ] No verifier is asked an existential question (text search: "exist" appears in coder-facing
      wording nowhere).
- [ ] VO-STRUCT verification defined as quote-location in immutable components from both baseline
      runs; VO-DEFECT verifier sees certificate + immutable materials only, never J1 outputs.

## Data-flow prohibitions (extends the Study-1 audit pattern)
- [ ] Tooling reads no Round-2 submissions/results, no writer_output_ACCEPTED, no Study-1
      case-level results; Study-1 machinery imported as code only.
- [ ] The 90 development tasks appear only in the exclusion list.
- [ ] No API-evaluation call path exists in Study-3 tooling.

## Reporting
- [ ] Reported set matches §7 exactly; no extra metric, no threshold.
- [ ] DS witnesses (the S′ texts) listed as a released artifact.
- [ ] Sampling CIs labelled as sampling; identification width labelled as P(UR); measurement
      disagreement labelled as such — one table, three named columns, no merging.
