# Interpretation Note 2 — GAP-5 ruling: routing of UNREPAIRABLE_FIRST_SUBMISSION

Status: pre-outcome execution interpretation / tooling amendment. Ruled and frozen
2026-08-30, **before any writer output exists** — the writer package is built after this
note, no writer session has started, no candidate S′ exists, no S′ coding run exists.
The frozen protocol (`548addbd…`) and its history are not rewritten. Companion to
Amendment 3 (`AMENDMENT_3_study3_native_resubmission_gate.md`), whose clause 6
identified GAP-5 as open.

## The gap

Amendment 3's gate produces a third terminal state, UNREPAIRABLE_FIRST_SUBMISSION, in
which the first writer submission stands permanently as the formal writer output but has
never passed the frozen candidate validator. The frozen protocol defined how such a task's
*outcome* falls (never DS without a witness profile; VO only via an independent §6
certificate; else UR) but did not define whether such a task consumes S′ verification
slots or how the scorer reports the state. GAP-5 closes this.

## Ruling (binding, verbatim clauses)

For UNREPAIRABLE_FIRST_SUBMISSION:

1. The task remains permanently in the confirmatory measured-eligible denominator `m`.
2. That first submission is permanently retained as the formal writer outcome.
3. Because no candidate S′ passed the frozen mechanical contract, the task does **not**
   enter the S′ blinded verification runs.
4. It is never recorded as DS.
5. The frozen VO-STRUCT / VO-DEFECT certificate pathway — fully independent of candidate
   validity — remains available; a valid certificate yields VO.
6. Absent a valid independent VO certificate, the task is UR.
7. No task substitution, no supplemental draw, and no promotion of sensitivity-only tasks
   to save verification slots.
8. The final scorer implements this routing mechanically and reports a separate
   `procedure_invalid_candidate` count — a **procedure diagnostic, not a fourth epistemic
   outcome**.

## Mechanical encoding (what the tooling now does)

**Routing unit is the whole submission — read off the frozen gate, not invented here.**
The frozen candidate validator accepts or rejects a *submission*; the S′ packet builder
(`build_study3_sprime_packets.py`, frozen) refuses to build unless a validator-accepted
`study3_writer_ACCEPTED.json` exists with a matching frozen hash. The gate
(`resubmission_gate_study3.py`, frozen) terminates the entire resubmission pathway on any
unrepairable flag. Consequently exactly two terminal states are mechanically reachable:

- **Accepted path**: an accepted writer output exists → every eligible task carries a
  contract-passing candidate → all enter S′ verification → `procedure_invalid_candidate`
  is empty. (The gate report's per-task `flag_repairable` labels are diagnostics only;
  acceptance is submission-level.)
- **Unrepairable path**: the terminal verdict is UNREPAIRABLE_FIRST_SUBMISSION → no
  accepted output exists, the S′ builder structurally cannot run (clause 3 holds by
  construction), and **every** task in the submission is `procedure_invalid_candidate`:
  ds = false for all (clause 4), VO certificates derive as always from baseline runs and
  immutable materials only (clause 5), remainder UR (clause 6).

This whole-submission granularity is the only reading the frozen artifacts support; it is
also the conservative one — it can only widen the UR band, never manufacture DS.

**Freeze convention for the unrepairable path** (used only if that path occurs): the
gate's `--delta` report is frozen as `writer_handoff/GATE_UNREPAIRABLE_FROZEN.json` with
its hash recorded in `writer_handoff/SHA256SUMS_WRITER_FROZEN`.

**Scorer (`score_study3.py`) changes, in force from this note:**

- `score()` takes a `procedure_invalid` task-id set. Such tasks classify as
  `classify(False, vo)`; a procedure-invalid task appearing in the S′ derivation is a
  HARD STOP (contradiction: it entered runs it was barred from).
- `main()` requires exactly one of `ds_derivation.json` (accepted path) or a
  hash-verified `GATE_UNREPAIRABLE_FROZEN.json` whose verdict field reads
  UNREPAIRABLE_FIRST_SUBMISSION (unrepairable path → `procedure_invalid` = all eligible
  tasks). Both present, or neither, is a HARD STOP — absence of data is never silently
  routed.
- The report carries `descriptive.procedure_invalid_candidate` (count + task ids) with
  the fixed sentence: procedure diagnostic, not a fourth epistemic outcome; tasks remain
  in `m`, are never DS, and classify VO/UR via the independent certificate path.
- On the unrepairable path the writer-declaration descriptive distribution is not
  computed (the formal writer output never passed the validator and may not even parse);
  the report says so instead of parsing unaccepted bytes.

Clause 7 needs no new code: the selection tool refuses redraws, the eligibility manifest
is frozen, and sensitivity-only membership never enters any confirmatory path (frozen
protocol + CR-1).

## Paper disclosure

As with Amendment 2 and Amendment 3: this ruling was introduced after formal selection
and after baseline eligibility derivation, but before any writer output, S′ coding
outcome, or DS/VO/UR classification existed.
