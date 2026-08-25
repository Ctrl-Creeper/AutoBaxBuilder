# Specification-writer handoff — Round 2

Everything a fresh session needs to author 90 candidate specifications, and nothing that would tell
it what the study is about or how any task is expected to turn out.

| artefact | value |
|---|---|
| Round-2 protocol | `4ca61b25973be20beec9cad085a7da503d600fdb7f427eb0e4251c3e02eb45da` |
| Round-2 selection | `76fb71636427725be2b7bc8bb2d4e110414e92cfbd9f8ef0ba2babdd578ad36e` |
| Writer package | `5a0e62c540fc4a16bff028e869262febb84b0a4918f88a4346947e123837278c` |

---

## The blind boundary, and why it is not "as little as possible"

The writer is shown **both case lists, with their labels**. The rewrite is defined relative to them —
keep List A settled, leave List B open — so withholding the labels would not blind the writer, it
would make the task impossible. The boundary is set by what the writer's job requires, not by
minimising what they know.

That is the opposite of the coders' packet, where the same cases arrive merged, shuffled and
unlabelled, because the coders' job is to judge each case without knowing its kind.

Withheld from the writer, because none of it bears on the rewrite: any coder judgement, the earlier
development round and its provenance, the classification vocabulary, expected proportions, the CWE
identifier, and the true task index.

## What goes where

| path | who sees it |
|---|---|
| `writer_package/INSTRUCTIONS.md` | writer |
| `writer_package/tasks/W01…W90.md` | writer |
| `writer_package/output_template.json` | writer |
| `validation/check_writer_package.py` | you, before and after authoring |
| `sealed/_KEY_DO_NOT_SHOW_WRITER.json` | **never** the writer — blinded id → task index |
| protocol v2, the selection manifest, every Round-1 artefact | **never** the writer |

## Contamination check

Run before handing anything over:

```
python docs/preregistration/2026-08-25_writer_handoff/validation/check_writer_package.py
```

The **primary** check is provenance, not vocabulary: every task file is rebuilt from its source
record and compared byte for byte, which proves the package holds exactly what the builder derived
from the frozen selection and the fixed template. A keyword scan cannot carry that argument — this
project has already shown that lexical absence does not imply informational absence — so the token
scan is present but labelled secondary. The two hand-authored files, which cannot be regenerated, are
checked for independence by 8-gram overlap against every withheld document.

Passing at freeze: 90 files regenerate byte-identically, the mapping covers the frozen selection
exactly, only the expected files ship, no shared 8-gram with any withheld document, and the manifest
matches disk and pins the selection by hash.

## Running it

1. **Isolate.** Copy `writer_package/` outside this repository and start the session with that
   directory as its working directory. If the session can read this repo it can find the protocol,
   the key and the earlier round by grep. Isolation is the blinding.
2. **Start** with `STARTUP_PROMPT.txt`.
3. **Collect** `writer_output.json`.
4. **Freeze in one step.** All 90 arrive together, then the file is hashed and committed. There is no
   partial submission and no revision afterwards — in particular, nothing is revised once the coding
   runs report, and coder disagreement is never a reason to reopen a specification.
5. **Build the coder packets from the frozen writer output**, mechanically. The packet builder
   consumes `writer_output.json` as it stands; it does not regenerate, clean, normalise or improve a
   specification. Any defect found at that point is recorded, not silently repaired.

## Invariants this handoff enforces

- The writer produces candidates only. **It never classifies a task**, and no category vocabulary
  appears anywhere in its materials.
- **No task may be dropped** — not for awkwardness, not because no clean candidate exists. Every task
  gets a candidate plus, where applicable, a structured failure code.
- When the rewrite cannot be done, the writer records a code from a **fixed taxonomy** rather than
  adjusting the transformation rule to make the task work.
- Original and candidate are both retained, with **per-clause edit provenance**: field, original text,
  action, replacement, and what the clause settled.
- Signature, setup code and every case are **frozen and copied mechanically**. They are never retyped
  by the writer, so they cannot drift.
- The writer neither runs nor sees any coding run.

## Failure taxonomy

`F1_LIST_COUPLING`, `F2_SIGNATURE_CARRIER`, `F3_PREAMBLE_CARRIER`, `F4_RETURN_CONTRACT_CARRIER`,
`F5_MATERIAL_DEFECT` — defined in `writer_package/INSTRUCTIONS.md` §4.

A failure code records what blocked a rewrite. **It is not a classification**, it is sealed from the
coders, and it may not be used as a label in analysis.

## Reserve

The selection's reserve list stays frozen as committed at `e7ae0c1`. A writer failure code is **not**
a reserve activation condition: the frozen conditions are mechanical construction failures only, and
no condition may be added now. A task the writer could not rewrite still goes to the coders with the
writer's best candidate.
