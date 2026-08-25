# Pre-adjudication record — instrument validation phase

Computed by `validation/validate_coder2.py score` against submission
`536d8824…` (frozen at commit `dde8fcc`) under protocol `84ec0d47`.

**No adjudication has been performed.** Nothing below resolves a disagreement.
Two defects found in the study materials are recorded so that adjudication, when
it happens, is not conducted against a record that hides them.

## Material defect 1 — the witness was shown as an incomplete function body

The packet showed each witness as the benchmark's `vulnerable_code` slot alone.
It omitted `code_after`, which in 5 of the 12 tasks carries the function's
`return` statement or its exception handler:

| task | index | omitted |
|---|---|---|
| T03 | 1364 | `except KeyError: return False` |
| T05 | 1083 | a following function definition |
| T07 | 1072 | `return profile` |
| T08 | 1067 | `return vehicle_info` |
| T12 | 434  | `except ConnectionError: return None` |

The second coder judged T07 and T08 non-compliant because the body mutates in
place and returns nothing, against a Return field promising the updated
dictionary. That reasoning is correct on the material shown, and the material was
wrong: the complete implementation does return the dictionary.

J2 is therefore unsound for at least T07 and T08, and its soundness is not
established for T03, T05 and T12. **J1 is unaffected** — the specification was
shown complete. The first coder is unaffected: gate 2 there ran the assembled
program through the runner, not the fragment.

The defect is in `scripts/build_coder2_packet.py`, which passes
`ground_truth["vulnerable_code"]` to the packet while `build_program()` in the
runner assembles `setup + code_before + body + code_after`.

## Material defect 2 — J3's wording is ambiguous

Three tasks (T03, T05, T06) were computed SEPARABLE — every capability case
determined, no safety case determined, witness compliant — while the same coder
answered J3 "cannot construct such an `S'`". Those are inconsistent: the
specification in front of them already had the profile J3 asks whether they could
achieve.

The likely reading is that J3 was taken as "can you write a *different* `S'`"
rather than "does such an `S'` exist". The protocol's computation rule does not
consult J3 on that branch, so the inconsistency passed silently.

Exposing an ambiguous definition is what this phase is for. Any repair produces
**v2** of the protocol, separately frozen, under which **both** coders recode.

## Numbers as computed, defects included

| | |
|---|---|
| coder-2 derived classification | SEPARABLE 7, INSEPARABLE 3, UNRESOLVED 2 |
| agreement with `fcf1120` | 6/12 |
| capability cases called determined | 0.79 |
| safety cases called determined | **0.00** (0 of 20) |
| tasks where safety determined < capability determined | 10/12 |

The two UNRESOLVED rows are T07 and T08 — both produced by the J2 defect above.

## Not yet computed

Cohen's κ on case determination, κ on J2 and J3, and quote concordance
(protocol §6 items 1, 2, 4) are not in this record. κ requires the first coder's
per-case determinations, which the first-coder round never produced: it recorded
per-task gate outcomes, not per-case judgements. Producing them now would be a
first coder who has seen the second coder's answers, so it cannot be done in this
phase. This is a gap in the first-coder round, recorded rather than patched.
