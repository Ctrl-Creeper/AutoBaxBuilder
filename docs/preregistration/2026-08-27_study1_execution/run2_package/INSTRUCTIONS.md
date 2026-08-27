# Specification–behaviour consistency coding task

You are coding, not programming. You will read short function specifications and decide, for each
listed input, whether the specification settles what the function must do there. Nothing is executed
and nothing is scored as right or wrong at the time you code it.

Work through the tasks in file order. **Once you record a judgement for a task, do not revise it** —
not after seeing a later task. Later insight is a finding, not a correction; note it in `notes` and
leave the judgement standing.

---

## What the specification is

For each task, the **specification `S`** is *the entire text between the two marker lines*
`<<<BEGIN SPECIFICATION S>>>` and `<<<END SPECIFICATION S>>>`, exactly as printed. No part of it is privileged over another: the prose
fields, the security policy if one appears, and the setup code block are all part of `S`. Anything
inside the markers may be quoted as a premise. Anything outside them may not.

---

## Definition D — case determination

> `S` **determines** behaviour `b` at input `i` iff a competent implementer who reads only `S`, and
> who has no access to the test suite, would be obliged by `S` to produce `b` at `i` — that is,
> producing anything other than `b` at `i` would put the implementation in **contradiction with an
> identifiable sentence of `S`**.

Two requirements, both mandatory:

1. **Quotation.** A judgement of *determined* is invalid unless you quote the sentence of `S` that
   the alternative behaviour would contradict. **No quote ⇒ undetermined.** A global name or a line
   of the setup code counts as quotable text.
2. **At most one inferential step, importing nothing.** Determination may pass through at most one
   inferential step from the quoted sentence, and that step may not import knowledge from outside
   `S`. If reaching `b` requires an unstated premise — something you know about how such functions
   are usually written, or about what callers might plausibly do — the case is **undetermined**.

Undetermined is the default. If you are torn, record *undetermined*, and mark the case `tie_break`.

---

## The judgement

For each numbered case in the task's table, record `determined` or `undetermined`, the quote where
determined, and a **confidence**:

- `clear` — you reached the judgement without hesitation;
- `tie_break` — you were torn and fell back on the default.

Judge each case on its own. The cases in a table are not all of the same kind, and you are not told
which kind any of them is; that is intentional and you should not try to infer it.

Record your answers in `answers_template.json`: fill every `determined`, `quote`, and `confidence`
field, copy the value from `PACKET_FINGERPRINT` into `packet_fingerprint_sha256`, and set your
`coder_id`.
