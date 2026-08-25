# Instrument Development Round 1 — permanent status marker

**These twelve tasks are Instrument Development Round 1. They are permanently excluded from every
calibration, measurement and experimental set that follows.**

The exclusion is unconditional and does not lapse. It holds even if a task looks unproblematic, even
if a later protocol would classify it differently, and even if the corpus is short of tasks. Any
document that reports a number drawn from these twelve must say that it came from Round 1.

## The tasks

SeCodePLT indices 666, 813, 1364, 643, 1083, 681, 1072, 1067, 893, 1350, 816, 434 — presented as
T01–T12 in `coder_package/tasks/`. The mapping is in `sealed/_KEY_DO_NOT_SHOW_CODER2.json`.

## Why they are burned

1. They were selected, transformed and coded *while the protocol was being written*. Definition D,
   the definition of *S*, and the three-carrier account were all derived partly from looking at
   them. A rule developed on a sample cannot be validated on that sample.
2. Coder 2 has now seen all twelve and can no longer serve as a blind coder on them.
3. Coder 1 authored the specifications and the obstruction claims.
4. Two of the twelve were coded against defective material (the witness fragment), and one
   classification is an artefact of a rule that v2 changes.

## What Round 1 established, and what it did not

Established:

- The three-carrier account — prose, signature parameters, setup globals — was **independently
  reproduced** by a coder blind to the study's direction, on all four tasks where a structural
  carrier had been claimed.
- A coder blind to the distinction separated capability from safety cases in 10 of 12 tasks
  (18/23 vs 0/24 determined). The construct appears codeable.
- Two concrete defects in the instrument, both found by scoring rather than by inspection.

Not established, and not to be cited from Round 1:

- Inter-rater reliability. It was never computable here.
- Any prevalence figure for separability in SeCodePLT or anywhere else.
- Which coder was right on any of the six disagreements.

## Frozen artefacts

| artefact | hash / commit |
|---|---|
| Protocol v1 | `84ec0d47…` |
| Coder package | `64954f80…` |
| Coder 1 result | `fcf1120` |
| Coder 2 submission | `536d8824…`, frozen at `dde8fcc` |
| Pre-adjudication results | `39fd117` |

None of these is to be edited. Corrections go in new documents.
