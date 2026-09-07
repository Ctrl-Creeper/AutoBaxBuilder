# Study 3 VO-STRUCT pre-existing executability audit

Date: 2026-09-07 (Asia/Taipei)

Status: frozen static ruling. This gate did not execute VO certificate derivation or the
final scorer.

Audit base: commit `9a378e3c396ecf5f710002332193a1294897c6ec` (the frozen DS-only
result). The audit was limited to protocol and source inspection plus checksum verification.
No task-level DS status, non-DS membership, S-prime judgement or quote, writer obstruction
declaration, or candidate content was inspected.

## Frozen pins and pre-existing inputs

| Item | Frozen SHA256 / verification |
|---|---|
| Study-3 protocol | `548addbd9277dbe901b8e1e599fdf3a6d4ef97e286610dbecc40bf1f5f5f81d7` |
| `vo_certificates.py` | `6bc60024915a81b88b866300adb7e3c7ca255a0f82333d858a91462bcd05df4a` |
| `score_study3.py` | `2425c8d10938b9828a2bca625366483408ec69e28eb2a412e6db809bb48dd8db` |
| Eligibility manifest | `a9db938ba633bc400ac035d9a200501c8bb7c70986f9b38c2e964885f483f3a6`; 1/1 checksum PASS |
| Frozen baseline submissions | 2/2 checksums PASS |
| Baseline packets and sealed mapping | 188/188 checksums PASS |
| Frozen case materialization | 2/2 checksums PASS |
| Frozen tooling | 31/31 checksums PASS |
| Confirmatory universe | `m=53`; eligible-list length 53 |

The VO tool was frozen before the formal draw. Its last substantive VO implementation predates
the DS reveal. The protocol, Interpretation Note 1, tooling self-test fixtures, and data-flow
audit all pre-existed the reveal.

## S1-S6 ruling

### S1 - PASS: every VO-STRUCT predicate was fully and mechanically defined

The frozen path applies the following predicates without a new judgement layer:

1. Iterate a task in the frozen measured-eligible universe.
2. Select a case whose sealed source-order role is `safety`.
3. Require that the same source case was judged determined in both frozen baseline runs.
4. Require each run's supporting quote, after frozen normalization, to locate in an immutable
   carrier: setup, function-name segment, closing instruction, or an exact original parameter
   name extracted by the frozen def-line rule.

These are the protocol section 6 VO-STRUCT sufficient-certificate predicates implemented by
`align_runs`, `param_names`, `immutable_only`, and `vo_struct`.

### S2 - PASS: all predicate inputs are pre-existing frozen materials

The inputs are the frozen eligibility manifest, the two frozen baseline submissions, their
sealed case-role mapping, and immutable benchmark segments/parameter names. The frozen case
manifest is the sole downstream case source. VO-STRUCT requires no newly authored certificate,
annotation, attestation, threshold, or human judgement.

### S3 - PASS: a frozen full-universe executable path exists

`vo_certificates.py::main` loads and hash-checks the frozen baseline submissions, aligns the two
runs, constructs immutable carriers, and calls `derive` over every ID in
`eligibility_study3.json`. `derive` calls `vo_struct` uniformly for the complete 53-task
confirmatory universe. The currently absent `vo_defect/` input leaves the separately closed
VO-DEFECT branch without any certificate to consume; no VO-DEFECT artifact may be added.

No part of that path was executed in this audit.

### S4 - PASS: VO-STRUCT is blind to constructive outcomes

The frozen VO construction path names or reads no DS derivation, non-DS membership, S-prime
submission, S-prime verifier failure pattern, S-prime verifier quote, candidate, or writer
artifact. Its judgement evidence is exclusively the independently frozen baseline evidence
required by the pre-existing VO-STRUCT rule. The frozen data-flow audit also places
`vo_certificates.py` in the writer-blind execution set.

### S5 - PASS: no result-conditioned discretion is required

The executable predicates contain no tunable threshold, interpretation hook, exception,
fallback, adjudication, or tie-break. Quote normalization and immutable-carrier location rules
were frozen before outcomes.

### S6 - PASS: predicate failure remains sufficient-certificate failure only

Interpretation Note 1 ruling 3 fixes failure semantics: a failed VO-STRUCT predicate means only
that no VO-STRUCT certificate was established. It does not establish separability, absence of
obstruction, or any other substantive conclusion. With VO-DEFECT closed, unresolved tasks remain
UR.

## VO-DEFECT disposition and provenance

VO-DEFECT remains closed and was not executed. The prior Q4 pre-execution audit found that the
preregistered consumer lacked a frozen independent evidence-production and attestation
procedure. No repair, new attestation workflow, certificate, or independent verification was
created.

Methodological provenance:

> VO-DEFECT was not executed because pre-execution audit found that the preregistered consumer
> lacked a frozen independent evidence-production and attestation procedure. No absence of a DS
> witness was treated as evidence of nonexistence.

This is an execution/instrumentation limitation and does not alter the frozen DS-only result.

## Outcome firewall

Allowed data flow for a later separately authorized VO-STRUCT gate is limited to the frozen
eligibility universe, frozen baseline submissions and sealed mapping, frozen immutable benchmark
materials, frozen case manifest, protocol, and frozen tooling. The VO output may be produced only
by the already frozen mechanical predicates.

Forbidden data flow includes DS status, non-DS membership, S-prime submissions or quotes,
candidate content, writer declarations or obstruction rationales, outcome-conditioned task
selection, new annotations, and any VO-DEFECT certificate or attestation.

During this audit, no formal VO output or final scoring output was created. The prior 36/36
data-flow audit remained PASS. No protocol execution deviation occurred.

## Final ruling

`VO_STRUCT_AUTHORIZED_LATER`

S1-S6 are all PASS. A later independent gate may run only the pre-existing frozen VO-STRUCT
path over the complete confirmatory universe. VO-DEFECT remains closed. This ruling itself does
not execute VO, establish any task-level certificate, or change any substantive result.
