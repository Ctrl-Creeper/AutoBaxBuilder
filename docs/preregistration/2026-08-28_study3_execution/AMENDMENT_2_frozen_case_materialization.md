# GAP-3 Amendment 2 (2026-08-29) — Frozen Case Materialization

**Nature.** Dated amendment resolving GAP-3 (`GAP3_report.md`, commit `45ffb8e`), issued
after the formal random selection (`b194696c…`, commit `382d1f7`) but **before any coder
exposure and before any baseline outcome exists**. The frozen protocol (`548addbd…`) is not
rewritten; this amendment adds one execution stage and supersedes one tooling invariant.

## Binding clauses (ruling verbatim in substance)

1. The formal selection manifest `b194696c…` remains unchanged: all 90 selected tasks stay
   in the study. No exclusion, substitution, redraw, supplemental recruitment, eligibility
   assignment, DS/VO/UR assignment, or task-specific exception is permitted because of
   GAP-3.
2. The quarantined prevalidation build (`3ea64b31…`) is provenance only; it never becomes a
   coding artifact or a source of formal case values.
3. Before baseline packets are rebuilt, one formal **case-materialization stage** covers
   all 90 selected tasks — not merely the three statically identified proc_exec tasks.
4. The already-frozen benchmark case extractor runs **exactly once per selected task** in
   one documented controlled environment; the complete case objects — inputs and expected
   behaviour b — freeze into a sealed **FROZEN_CASE_MANIFEST**.
5. The environment record captures: benchmark/source pins, interpreter/runtime version,
   OS identity, working-directory construction, relevant environment variables,
   locale/timezone, and sha256 of mechanically identifiable files/resources read by the
   extractor. The materialization timestamp is provenance, never an input to any rerun.
6. No normalization, sanitization, canonicalization, repair, or hand-editing of oracle
   values: formal b is exactly what the pinned extractor produced during the one
   authorized materialization.
7. Sensitive/environment-derived raw values live only in the sealed manifest. Public/audit
   artifacts carry hashes and dependency metadata — no raw `/etc/passwd`, directory
   listings, credentials, or comparable host material.
8. After the manifest freeze, **no downstream Study-3 component re-executes testcase
   extraction** to obtain or verify case values. Baseline builder, provenance audit,
   sealed-key construction, S′ verification, and final scoring all consume the same frozen
   manifest.
9. The former "fresh extraction must byte-equal packet cases" invariant is **superseded**
   by: packet case object ≡ FROZEN_CASE_MANIFEST case object, byte-for-byte.
10. The manifest is immutable after freeze. A later mismatch is a hard stop; it never
    triggers rematerialization.
11. If the authorized materialization itself fails for any selected task (exception,
    timeout, missing dependency, incomplete ⟨i,b⟩ serialization): hard stop **before**
    freezing the manifest; no task-level handling rule is invented at that point.
12. The 764-frame GAP-3 scope statistics remain outcome-blind structural characterization
    only. proc_exec membership, stability probes, network-import flags, etc. enter no task
    selection, eligibility, writer behavior, DS/VO classification, or subgroup outcome
    analysis unless separately designated exploratory after the confirmatory analysis is
    frozen.
13. **Paper disclosure clause:** the paper must disclose that Amendment 2 was introduced
    after formal random selection but before coder exposure/outcome observation, because
    the original extraction-reproducibility assumption was falsified during packet audit.

## Implementation (this commit)

- `materialize_cases.py` — the one authorized materialization; `--approved-materialization`
  guard; immutable-manifest guard (clause 10); clause-11 hard stop writes nothing on any
  failure; clause-5 environment record; clause-7 sealed/public split (sealed manifest is
  kept out of version control like the quarantined build; its hash freezes in
  `SHA256SUMS_MATERIALIZATION` and in every downstream sealed key).
- `study3_pins.load_case_manifest()` — hash-verified sole case source for every consumer.
- `packet_build.build_packages` now requires `cases_by_index` and cannot extract;
  `build_study3_baseline_packets`, `build_study3_writer_handoff`,
  `build_study3_sprime_packets`, `vo_certificates` all consume the manifest and pin its
  hash where they build sealed keys.
- `audit_baseline_packets.py` re-anchored to the clause-9 invariant (packet ≡ manifest);
  it no longer re-executes extraction.
- `dataflow_audit.py` mechanically enforces clause 8: the literal `extract_cases` may
  appear in `materialize_cases.py` only, across all execution files.
- Self-test extended (59 checks): materializer pass-through, clause-11 failure input,
  public-artifact hash-only shape, host-resource hashing, builder refusal on a
  manifest-missing task, materialization guard.
