# Study 1 blinded coding — execution deviation record

Frozen with the submissions. One deviation occurred; nothing else departed from the frozen chain.

## D1 — external quota interruption and same-session resume (2026-08-27/28)

Both blinded runs were terminated mid-task by an external API session limit ("session limit,
resets 12:20am Asia/Taipei") — an infrastructure event, not a coding outcome and not a stop-rule
trigger. State at interruption, measured by a count-only probe that read no judgement content:
run1 at 264/442 recorded cases, run2 at 372/442.

Handling, chosen against the alternatives of restarting fresh sessions or editing anything:

- After the quota reset, each run's **own session** was resumed from its transcript with a
  **byte-identical, content-neutral message** instructing it to continue per the frozen
  STARTUP_PROMPT from the first unfilled case, and **not to revise any judgement already
  recorded** (the packages' frozen no-revision rule).
- No packet, tooling, instruction, or template was modified. No information about the other run,
  about progress, or about any judgement was included in the resume message.
- The orchestrating session learned only the fill counts above; no quote, judgement, or note was
  read before both submissions were frozen.

Consequence for interpretation: each run's judgements were produced across two sittings of the
same session with an interruption between them. The interruption point is recorded here so any
later analysis of position effects can condition on it; the interruption was position-correlated
(file order), identical in kind for both runs, and blind to content.

## Non-deviations, recorded for completeness

- Working-directory package files re-hashed after coding: all 93 files per run byte-identical to
  the frozen SHA256SUMS_PACKETS. The inputs did not change.
- Each submission was validated in isolation with the frozen validator and frozen immediately
  (run2 first: `3401bf6f…`, commit `06be7ee`, while run1 was still blinded and in progress;
  then run1: `ebb0e187…`). Neither run received any information derived from the other at any
  point. The sealed key remains unopened; the scorer has not run; no prevalence or reliability
  number has been computed.
