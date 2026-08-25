# Second-coder handoff — instrument validation phase

Everything needed to have a fresh session produce an independent second coding, and nothing that
would tell it what the study is about.

Frozen protocol governing this phase:
`docs/preregistration/2026-08-25_instrument_validation_protocol.md`
sha256 `84ec0d4756374e756b5bb0f1e52e11b0e6846db53d07797ddae26924c1027431`

Coder package: `coder_package/`, sha256 `64954f807d6c21d6a1719113d98ae4a57b5de767883c6b235a18e13d1ba62a9f`
(rolled over the per-file manifest in `coder_package_manifest.json`).

---

## What goes where

| path | who sees it |
|---|---|
| `coder_package/INSTRUCTIONS.md` | second coder |
| `coder_package/tasks/T01…T12.md` | second coder |
| `coder_package/answers_template.json` | second coder |
| `validation/validate_coder2.py` | you, after submission |
| `sealed/_KEY_DO_NOT_SHOW_CODER2.json` | **never** the coder — task identity + capability/safety labels |
| `sealed/coder1_fcf1120_classifications.json` | **never** the coder |
| `sealed/PROVENANCE_instrument_development.md` | **never** the coder |
| the frozen protocol itself | **never** the coder |

**The protocol is deliberately not in the coder package.** It names the benchmark, the CWE
identifiers, the counts, and the answer to J3 on several tasks. The coder gets a derived instruction
document carrying Definition D and the J1–J3 procedure and nothing else.

---

## One substitution you should approve or veto

Definition D's **operative** wording is reproduced in `INSTRUCTIONS.md` unchanged. Its *illustrative*
example was replaced, because the original would have disclosed the domain. Frozen protocol §1:

> If reaching *b* requires a premise such as **"an attacker may supply a crafted path"**, the case is
> **undetermined**.

Instructions as issued:

> If reaching `b` requires an unstated premise — **something you know about how such functions are
> usually written, or about what callers might plausibly do** — the case is **undetermined**.

The rule (one step, importing nothing from outside `S`) is identical. Only the example changed. The
protocol's own text is untouched, so `84ec0d47` still verifies. Say the word and I will re-issue with
a different neutral example, or with the original if you would rather accept the disclosure.

---

## Running it

**1. Isolate the package.** Copy `coder_package/` somewhere outside this repository and start the new
session with that directory as its working directory. If the session can read this repo it can find
the protocol, the sealed key, and the first coder's answers by grep. Isolation is the blinding.

**2. Start the session** with the prompt in `STARTUP_PROMPT.txt`.

**3. Collect** `coder2_answers.json` from that session.

**4. Verify and freeze — before looking at anything.**

```
python validation/validate_coder2.py verify /path/to/coder2_answers.json
```

Fails on any missing entry, and on any case marked *determined* without a quote (invalid under
Definition D). On success it prints the submission sha256. **Record that hash** — commit it — before
step 5. `score` refuses to run against a submission whose hash does not match, so the ordering cannot
be skipped by accident.

**5. Reveal the key and compute.**

```
python validation/validate_coder2.py score /path/to/coder2_answers.json --frozen-hash <sha256>
```

Emits the derived classification per task, the discrimination check, the comparison against
`fcf1120`, and writes `results_pre_adjudication.json`. It stops there by design.

**6. Then, and only then, adjudicate.** Separate step, separate commit. Neither coding is edited to
match the other.

---

## Fixed order, for the record

```
coder-2 output → hash & freeze → reveal key → compute agreement, quote concordance,
derived classification → save pre-adjudication results → compare to fcf1120 → adjudicate
```

`fcf1120` (first coder) and `84ec0d47` (protocol) are immutable. The task set is **not** expanded
beyond 12 until κ on J1 and the full disagreement table have been reported.

---

## What the second coder is not told

The benchmark's name, the CWE identifiers, the `security_policy` field, the original task
descriptions, which cases are capability and which are safety, the first coder's classifications and
counts, the words separable and inseparable, and the finding that the setup code carries obligations.

Capability and safety cases are merged and shuffled inside each task, so the capability cases act as
a control the coder cannot identify. The coder assigns no class; classification is computed from
J1–J3 by the scoring script.
