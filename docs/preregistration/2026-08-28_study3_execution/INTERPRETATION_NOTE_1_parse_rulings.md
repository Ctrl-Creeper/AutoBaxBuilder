# Interpretation Note 1 (2026-08-28, pre-draw) — rulings on the five mechanical parse decisions

**Nature of this document.** Pre-draw execution interpretation note, recorded before the
formal SRSWOR draw and before any Study-3 outcome exists. It changes no estimand, no sample
rule, no part of Definition D, no DS/VO criterion, and no observed outcome; the frozen
protocol (`548addbd…`, commit `75e7968`) is not rewritten. It fixes how the frozen tooling's
documented parse decisions are to be read, and encodes one hard-stop behavior.

## Rulings

1. **Eligibility both-agree = case-level intersection** — accepted as implemented:
   ∃ c ∈ Safety(t): D₁(c) = D₂(c) = 1. The L2 either-run profile remains sensitivity-only.
2. **Parameter extraction** by the frozen Round-2 `ground_truth.code_before` def-line rule —
   accepted.
3. **The four frozen VO-STRUCT predicates are SUFFICIENT certificate rules, strictly.**
   Failure to satisfy them implies only that no VO-STRUCT certificate exists — the task is
   UR absent another valid frozen VO class. Predicate failure **never** establishes
   separability, absence of obstruction, or anything else. (Consistent with the frozen
   error-flow property: everything undecided flows to UR.)
4. **Pre-draw fixed non-overlapping protocol-hash slices** for presentation randomization —
   accepted. They may not affect the `[0:8]` formal selection seed (and do not: the slices
   pinned in `study3_pins.SEED_SLICES` are disjoint, `[0:8]` is reserved to the draw).
5. **Round-2 resubmission gate: reuse exactly as frozen precedent, else HARD STOP.**
   If the frozen Round-2 gate's artifact/schema assumptions cannot be applied to the
   Study-3 writer submission as they stand, execution halts **before accepting or repairing
   that submission**. Incompatibility is NOT a deviation that permits execution to
   continue, and no replacement gate may be designed after writer output has been observed.
   (This supersedes the softer "recorded deviation" wording in the first README revision;
   the README is amended accordingly in the same commit.)

## Scope

Binding on Study-3 execution from this commit forward. No tooling code required changes:
rulings 1–4 confirm the implementation as frozen at `d5e5ee6`; ruling 5 is encoded here and
in README.md (documentation only — the gate-reuse path contains no code in this tooling).
