# CWEval cross-benchmark replication protocol (FROZEN 2026-08-28)

**Status.** Frozen mechanical instantiation of the Study-1 protocol §6.1 (`e4e08330…`), whose
parameters were pinned before any SeCodePLT prevalence number existed. **Execution has not
started**: no packet is built, no run is started, no case is coded, no CWEval prevalence is
computed. Any change after freezing is a dated addendum.

*Amended 2026-08-28, before any tooling existed: §2's inferential interpretation corrected — the
census estimand is the finite-frame prevalence, no sampling CI is reported for frame inference,
measurement uncertainty is primary, and bootstrap intervals are superpopulation/generalization
sensitivity only. The frame, Definition D, the coding procedure, the inclusion rules, and the
planned-replication status are unchanged.*

**Paper wording, binding:** this arm is a *"preregistered cross-benchmark replication using an
independently developed benchmark."* The benchmark is independently developed (B2); the **coding is
not described as fully independent**, because prior exposure exists and is disclosed: a structural
classifier ran over all 119 test files (the 62/119 count), and the `cwe_943_0` family was read at
case level and is pre-excluded from the frame. No stronger independence claim may appear anywhere.

**Design-input boundary.** The Study-1 SeCodePLT pre-adjudication result (`f823bf9`) is **not a
design input**. The sole SeCodePLT-derived quantities admitted are the two ICC planning values
0.577 / 0.572, admitted by the frozen §6.1 sample-size rule and transcribed here once. No CWEval
tooling may read any Study-1 result file; the phase-1 consistency check enforces this mechanically.

---

## 1. Frame

Enumerated by the benchmark's own rule (`generate.py::_get_cases`: `*_task` stem, extension in the
shipped `LANGS`, skip `__pycache__`), from the repo pinned in `cweval_frame.json`:

- 119 task files enumerated; **`cwe_943_0` family (5 files) excluded** per the frozen
  prior-exposure ruling → **114 eligible task files in 35 families**;
- **248 functionality cases, 186 security cases**, counted by the benchmark's own
  `pytest.mark.functionality` / `pytest.mark.security` marks (textual occurrence count, method
  recorded per file); zero files with structural issues;
- every enumerated source file and the three prompt-pipeline files are SHA256-pinned in
  `cweval_frame.json`.

**Cluster = family** (CWE id + variant number): language variants of a family share specification
content, so the family is the independence unit. Families carry 1–5 language variants.

## 2. Sample: census (GAP-1, recorded), and the census estimand

The frozen precision rule — worst-case (p=0.5) 95% half-width ≤ 0.10 on the safety stratum,
computed with the ICC planning values — requires 63–64 families; **35 exist**. §6.1 did not
prescribe the insufficient-frame branch. **GAP-1 resolution: census of the entire eligible frame**,
the only choice-free completion and one that introduces no post-result selection; the planning
arithmetic that established infeasibility is preserved in `sample_size_arithmetic.json` as a
record, not as a precision statement.

**Inferential interpretation (amended 2026-08-28, before any tooling or coding).** Because every
eligible family is coded, the formal CWEval estimand is the **finite-frame census prevalence** of
the frozen 35-family eligible frame — not a sample estimate of that frame. Consequently:

- **no sampling CI exists or is reported for inference to the eligible frame**, and no planning
  half-width figure may be presented as the sampling precision of the CWEval prevalence;
- **primary uncertainty is measurement uncertainty**, reported exactly as in Study 1: the two
  blinded runs separately, their mean, the [both, either] measurement-disagreement interval, and
  the preregistered reliability metrics (raw agreement, cluster-aware κ);
- family-cluster bootstrap intervals are retained but are labelled, everywhere they appear,
  **superpopulation / generalization sensitivity intervals** — sensitivity of the figures to
  regarding the frame as a draw from a hypothetical population of similar task families. They may
  **not** be used to claim uncertainty about the exact eligible-frame prevalence.

Because the sample is a census, **no selection randomisation exists or is needed**;
`selection_manifest.json` lists all 35 families / 114 files deterministically. Presentation
randomisation (task and case permutations) is a builder concern, seeded from this protocol's
hash exactly as in Study 1.

## 3. Estimand and measured object

Identical in form to Study-1 §3, with the benchmark's own boundaries:

- **S_t** = the verbatim default model-visible prompt: the task-file slice from the `BEGIN PROMPT`
  anchor to the `BEGIN SOLUTION` line (imports, signature, docstring) wrapped in the shipped
  `DirectPrompt.PPT` template with its per-language instruction (`cweval/ppt/__init__.py`; default
  `ppt='direct'` in `Gener.__init__`, pinned). **`SecurePrompt` is a non-default security-framing
  variant and is excluded from S_t**; it may never be mixed into default-prevalence material.
- Case = one `pytest.param(inputs…, expected_output)` entry; strata by the benchmark's own marks.
- Parameters: case-weighted **θ_saf (headline)**, θ_cap, θ_all over the eligible frame, per frozen
  Definition D applied to ⟨S_t, expected behaviour at the case's inputs⟩.
- Secondary, derived and brittle: family-level P(any security case determined).
- **No `security_policy` analysis** — no such field exists here; nothing is ported.

## 4. Coding, validation, scoring — symmetric with Study 1

- **Two fresh independent blinded coding runs**, J1 only plus the confidence field; frozen
  Definition D and J1 wording **verbatim** (the Study-1 packet INSTRUCTIONS text, unchanged apart
  from the task-count number); the specification is the entire text between the S markers; coders
  are never told case kinds, family structure, or what the tasks are for.
- Validator: schema / completeness / provenance (packet fingerprint) / quote locates in the
  presented S_t. No judgement of correctness.
- Scoring, one pass after both submissions are independently frozen: per-run θ, two-run mean
  (primary), measurement-disagreement interval [both, either] — the primary uncertainty statement
  per §2 — plus **family-cluster bootstrap intervals labelled as superpopulation / generalization
  sensitivity intervals only** (B=2000, seed = int(this protocol's sha256[:8], 16); never
  presented as finite-frame sampling CIs), raw agreement and cluster-aware κ (chance agreement
  within family, case-weighted), per-run ICC. No metric outside this list.
- Execution gates as in Study 1: tooling frozen with self-tests and a data-flow audit → explicit
  approval → packet build + audit → isolation preflight → runs → per-run independent validation
  and freeze → reveal + scoring. Deviations recorded, never patched.

## 5. Data-flow prohibitions (checked mechanically)

CWEval tooling and documents may read: the CWEval repo, this protocol, `cweval_frame.json`,
`selection_manifest.json`, and the two ICC constants above. They may not read or embed: any
Study-1 result value or result file, any Round-2 / writer / Study-3 artifact, or the SeCodePLT
sealed keys. `cweval_phase1_check.py` scans every phase-1 file for result values and banned
artifact names; the same scan extends to phase-2 tooling when it is written.
