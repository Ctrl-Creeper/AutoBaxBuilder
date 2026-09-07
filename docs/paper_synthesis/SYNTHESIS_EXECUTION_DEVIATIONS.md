# Paper synthesis execution deviations

**Document type:** execution provenance for a non-preregistration synthesis gate.  
**Evidence cutoff:** Study 3 final freeze `8c39ad48f90f1369bf8729b3585cb17079349042`.

## DEV-SYNTH-1 - overbroad Study-2 aggregate projection

During cross-checking of already frozen Study-2 aggregate reliability values, a read-only `jq`
projection attempted to remove task-level keys by name before printing the remaining JSON. One
derived-class table used a different key from the exclusion list, so the command additionally
displayed part of that frozen Study-2 table.

Disposition:

- the displayed rows were not inspected for a substantive pattern, quoted, summarized, joined,
  classified, or used in any synthesis claim;
- no new statistic, subgroup, failure explanation, or task-level analysis was produced;
- no Study-3 confirmatory task, candidate specification, verifier judgment, quote, UR identity, or
  failure record was opened or displayed;
- the four synthesis documents contain no information derived from the unintentionally displayed
  rows;
- the aggregate verification was subsequently performed with direct, named aggregate-field
  projections only.

This is retained as a procedural read-scope deviation. It does not change any frozen result or the
claim-evidence ruling.

## DEV-SYNTH-2 - whitespace-sensitive consistency-check false negatives

The first invocation of `cross_document_consistency_check.py` returned `34/36 PASS` and wrote
`CROSS_DOCUMENT_CONSISTENCY_REPORT.json` with `HARD_STOP` status. Its two failed assertions searched
for exact continuous strings, while the substantively identical statements were line-wrapped in
Markdown. The failures concerned the `VO = 0` limitation and the coding-run/human-coder boundary;
both statements were present in the checked documents.

The failed report is preserved unchanged. The checker was amended only to collapse whitespace and
case for these two phrase checks and to write a separate
`CROSS_DOCUMENT_CONSISTENCY_REPORT_FINAL.json`. That invocation returned `35/36 PASS`: the
human-coder assertion passed, while the VO assertion still required the exact word `that`, which
neither of the two valid document phrasings uses. This second report is also preserved unchanged.
The predicate was narrowed to the actual semantic requirement - both an established-certificate
limit and an explicit nonexistence disclaimer must be present - accepting either frozen wording,
and its last invocation writes `CROSS_DOCUMENT_CONSISTENCY_REPORT_FINAL_V2.json`. No expected
result, source hash, numerical token, claim status, or synthesis document was changed in response.
