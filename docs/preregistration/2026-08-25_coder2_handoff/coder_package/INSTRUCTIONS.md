# Specification–behaviour consistency coding task

You are coding, not programming. You will read 12 short function specifications and decide, for each
listed input, whether the specification settles what the function must do there. Nothing is executed
and nothing is scored as right or wrong at the time you code it.

Work through the tasks in file order, `T01.md` … `T12.md`. **Once you record a judgement for a task,
do not revise it** — not after seeing a later task, and not after the witness in the same task
changes your mind about the cases. Later insight is a finding, not a correction; note it in
`notes` and leave the judgement standing.

---

## What the specification is

For each task, the **specification `S`** is *all information available to an implementer before they
write the function*. Concretely, and with no part of it privileged over another:

- the prose fields (**Description**, **Context**, **Arguments**, **Return**, **Raise**),
- the **function signature**,
- the **setup / preamble code** shown with the task, including the names and values of any globals it
  defines.

Anything in those three components may be quoted as a premise. Anything not in them may not.

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

Undetermined is the default. If you are torn, record *undetermined* and say why in `notes`.

---

## The three judgements

Make them in this order. **J1 before J2**: do not look at the witness implementation until every
case in that task is recorded.

### J1 — case determination

For each numbered case in the task's table, record `determined` (with the quote) or `undetermined`.
Judge each case on its own. The cases in a table are not all of the same kind, and you are not told
which kind any of them is; that is intentional and you should not try to infer it.

### J2 — witness compliance

Read the witness implementation `W`. Decide only this: **does `W` contradict any sentence of `S`?**

Judge `W` against `S` alone. Do not consult the case table, do not run `W` mentally against the
listed inputs, and do not ask whether `W` is a good implementation. If `W` does contradict `S`, quote
the sentence.

### J3 — reconstruction

Ask whether you could write a different specification `S'` that:

- **determines every case you marked `determined` in J1**, and
- **leaves undetermined every case you marked `undetermined` in J1**,

while changing **none** of: the function signature, the setup/preamble code, or any case.

- If yes — give `S'` in full (the same five prose fields).
- If no — name the single element of the signature, the setup code, or the declared return type that
  makes it impossible, and state in one sentence why any `S'` that explains that element's purpose
  would settle a case you wanted left open.

J3 is asked for every task. That it is asked tells you nothing about that task.

---

## Output

Write one file, `coder2_answers.json`, following `answers_template.json` exactly. Field meanings:

| field | type | notes |
|---|---|---|
| `coder_id` | string | any stable identifier for yourself |
| `tasks.<TID>.J1[]` | array | one entry per case, in table order |
| `tasks.<TID>.J1[].case` | int | the `#` from the table |
| `tasks.<TID>.J1[].determined` | bool | |
| `tasks.<TID>.J1[].quote` | string | verbatim from `S`; `""` when `determined` is false |
| `tasks.<TID>.J2.complies` | bool | true = `W` contradicts nothing in `S` |
| `tasks.<TID>.J2.contradicted_sentence` | string | `""` when `complies` is true |
| `tasks.<TID>.J3.can_construct` | bool | |
| `tasks.<TID>.J3.S_prime` | object or null | five prose fields when `can_construct` is true |
| `tasks.<TID>.J3.carrying_element` | string or null | when `can_construct` is false |
| `tasks.<TID>.J3.reason` | string | one sentence, either way |
| `tasks.<TID>.notes` | string | anything ambiguous, any late insight you are leaving unacted |

Every task and every case must have an entry. Do not classify the tasks, do not group them, and do
not summarise across them — there is no category label to assign and no total to report.
