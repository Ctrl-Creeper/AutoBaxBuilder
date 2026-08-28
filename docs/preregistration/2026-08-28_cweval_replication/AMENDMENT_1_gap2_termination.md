# Amendment 1 (2026-08-28) — termination of the CWEval confirmatory replication at GAP-2

**Nature of this document.** Dated protocol deviation/amendment to the frozen CWEval replication
protocol (`76d19809…`, commit `37c63a9`). The original protocol is preserved unaltered — history is
not rewritten — and this amendment supersedes its execution sections. It cites the GAP-2 report and
structural classification frozen at commit `fb7ae6f` (`GAP2_case_unit_report.md` `35443e03…`,
`gap2_structural_classification.json` `b720e0fb…`).

## Ruling

**The Definition-D confirmatory replication on CWEval is terminated. CWEval is reassigned to
complementary structural characterization.** The frame may not be contracted to structural class A
as a substitute formal replication, and no test-body semantic oracle extractor is developed for
this paper's confirmatory analysis.

## Fixed rationale — pre-outcome measurement incompatibility, not a prevalence result

- A formal replication requires that the frozen case object ⟨S, i, b⟩ be obtainable mechanically,
  without adding a new semantic measurement layer.
- The outcome-blind AST audit showed this requirement fails on the CWEval frame as a whole: 83% of
  security cases sit in structural classes with no mechanically explicit param-level expected
  behaviour.
- The original protocol's B1 compatibility assumption is thereby overturned by a census-level
  structural audit.
- This finding precedes any CWEval coder packet, any determination judgement, and any prevalence
  calculation. No outcome was observed before termination.

## Binding clauses

1. **Reporting language, fixed:** the planned replication was *attempted but terminated before
   outcome observation, because the preregistered measurement interface was incompatible with the
   benchmark's oracle representation.*
2. **No CWEval Definition-D prevalence is reported**, at any grade, in this paper.
3. **Class A (16 files / 32 security cases) is not used as a substitute confirmatory sample.**
4. **No B/C test bodies are read** to design a new semantic extractor for this confirmatory
   replication.
5. The outcome-blind A/B/C representation statistics already obtained (16/39/59 files;
   32/44/110 security cases; 11 non-literal param lists; the one counting-method disagreement)
   **may be reported as complementary structural characterization**, described explicitly as
   facts about **oracle representation structure**, never as specification-leakage prevalence.
6. **Provenance retained in full:** the `cwe_943_0` prior-exposure disclosure and exclusion, the
   original unconditional planned-replication decision and its outcome-blind eligibility table,
   the census/GAP-1 ruling and its finite-frame amendment, and the GAP-2 exposure ledger (AST
   structure only; no param values, test bodies, or S_t content read) all stand as the complete
   record of the attempt.
7. **CyberSecEval and BaxBench retain their prior complementary/origin positioning.** Neither is
   promoted to a confirmatory benchmark in consequence of this termination.

## Effect on the paper

The formal Determination-prevalence claim rests on the completed SeCodePLT arm (Study 1). The
cross-benchmark tier now comprises structural characterization of four benchmarks — CWEval's
oracle-representation structure (this amendment's clause 5), SeCodePLT's shipped-prompt structure,
CyberSecEval's linter-oracle structure, and BaxBench's procedure-level oracle structure — with the
attempted-and-terminated replication reported as such under clause 1. The termination itself is a
finding about measurement portability: a construct validated on one benchmark's oracle
representation does not automatically transport to another's, and the preregistered gate caught
that before any outcome could contaminate the decision.
