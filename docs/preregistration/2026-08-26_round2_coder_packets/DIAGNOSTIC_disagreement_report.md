# Diagnostic disagreement analysis — Round 2

**Diagnostic only.** Nothing is adjudicated, no disagreement is resolved, neither run is recorded as
correct, and protocol v2 is not touched. Every stratification below is mechanical: a quote is
attributed to a carrier by locating it verbatim inside the frozen specification, never by reading
what it means. No semantic similarity was computed.

Inputs: `alignment.json` `de66ae3f…`, both frozen submissions, `results_pre_adjudication.json`
`17300bb1…`. Produced by `diagnose_disagreements.py`.

---

## 1. The finding that reframes the rest: J3 carried no information

**Both runs answered `exists = true` on all 90 tasks. J3 is constant.**

Its zero disagreement is therefore not evidence of reliability — a constant cannot disagree. Two
consequences follow mechanically, and neither is an empirical claim about the tasks:

- **`STRUCTURALLY_CARRIED` and `INSEPARABLE` were unreachable.** Both branches of the frozen C3 table
  require `J3 = false`. The zeros in the derived-class marginals are a property of the routing, not a
  measurement of the corpus.
- The instrument's three-way structure collapsed, in this sample, to what J1 alone distinguishes.

Whether J3 is degenerate because the question is too coarse, because the candidate specifications
made constructibility obvious, or because the wording invites assent, is not decidable from these
data and is not decided here.

J2, by contrast, is not degenerate — 40/90 and 39/90 `contradicts_S` — and disagreed 7 times.

## 2. Directionality: 21 versus 7

| | coder1-only determined | coder2-only determined |
|---|---|---|
| capability cases | 15 | 5 |
| safety cases | 6 | 2 |
| carrier cited by the determining run | prose ×21 | prose ×7 |

The asymmetry is **not** concentrated in a case kind: both runs' base determination rates are
close and ordered the same way (capability 0.802 / 0.759, safety 0.376 / 0.356). The excess is a
uniform shift — coder1 determines slightly more of everything — rather than a disagreement about a
particular kind of case.

**Every one of the 28 disagreements cites prose.** Not one turns on the signature or the setup code.
The structural carriers, which the earlier development round found so consequential, produced no
disagreement at all here.

## 3. Confidence: no disagreement was clear against clear

| | disagreements | agreements |
|---|---|---|
| clear vs clear | **0** | 304 |
| clear vs tie_break | 13 | 42 |
| tie_break vs clear | 6 | 26 |
| tie_break vs tie_break | 9 | 42 |

Every disagreement involved at least one run that recorded itself as torn, and 304 of the agreements
were reached with both runs confident. On its face this locates disagreement at the boundary of the
definition rather than in the definition itself — but the tie-break instruction pushes a torn coder
toward *undetermined*, so `clear vs tie_break` and its mirror are also where the tie-break rule
itself is doing the work. Which of the two accounts holds is an adjudication question.

Tie-break rates differ between runs: 18.8% and 24.0%.

## 4. Quote divergence: most of it is span, not evidence

Of 246 cases both runs called determined, 73 cited different text. Classified by mechanism:

| mechanism | n |
|---|---|
| different extent of the same passage | 53 |
| different components | 7 |
| prose versus structural carrier | 7 |
| at least one quote not locatable in `S` | 5 |
| different sentences in the same component | 1 |

So the headline concordance understates agreement on evidence:

```
exact normalised match                 173 / 246 = 0.703
+ different extent of the same passage   53
= citing the same passage              226 / 246 = 0.919
genuinely different evidence            20 / 246 = 0.081
```

This is a re-partition of the same mechanical classification, not a new metric and not a similarity
threshold. Both figures are reported; neither replaces the other.

**Five quotes could not be located in `S` at all** (tasks C77, C89). The frozen validator required a
non-empty quote but never checked that it appears in the specification. That is a gap in the
instrument, recorded here; it is not repaired, and protocol v2 is not amended.

## 5. Task concentration

16 of 90 tasks carry all 28 case disagreements: one task with 4, one with 3, seven with 2, seven with
1. The top three tasks account for 32% and the top five for 46%. Disagreement is somewhat clustered
but not driven by a handful of pathological tasks.

## 6. What drove the 12 class disagreements

| driver | tasks |
|---|---|
| multiple J1 cases | 7 |
| a single J1 case | 3 |
| mixed inputs | 2 |
| J2 alone | 0 |
| J3 alone | 0 |

Three tasks changed class on **one** case judgement. That is the classification rule behaving as
written — `NOT_YET_BLINDED` turns on whether *any* safety case is determined — and it means
task-level class agreement is more brittle than case-level agreement.

## 7. Mechanism table

| stratum | observation |
|---|---|
| J3 | constant `true` in both runs; zero disagreement is uninformative; two derived classes unreachable |
| J2 | 40/90 and 39/90; 7 disagreements |
| direction | uniform +0.03 shift in coder1's determination rate, not concentrated in a case kind |
| carrier | 28/28 disagreements cite prose; 0 cite signature or setup |
| confidence | 0/28 disagreements were clear vs clear; 304 agreements were |
| quote | 53/73 divergences are span-length on the same passage; 20/246 cite genuinely different evidence |
| locatability | 5 quotes not present in `S`; validator did not check this |
| concentration | 16/90 tasks; top 5 tasks hold 46% |
| class drivers | 10 of 12 driven by J1 alone; 3 of those by a single case |

## 8. What this analysis does not establish

- Which run was right about anything.
- Whether the definition is sound, or merely applied consistently at its centre and inconsistently at
  its edge.
- Whether J3's degeneracy is a property of the question, of these specifications, or of the wording.
- Any prevalence claim. The derived-class marginals are conditioned on a J3 that never varied.
