# Frozen behavioural-strategy taxonomy — Study 4B post-hoc mechanism analysis

**This file is frozen before any completion is inspected or coded.** Its SHA-256
is recorded in `EXPLORATORY_MANIFEST.json`. Categories may not be added, removed,
or re-specified after coding begins.

## Coder

Coding is performed by a mechanical classifier (`study4b_exploratory.py`,
function `classify_code`) that receives **only** the extracted completion code
string and the target function name. It never receives the condition label, the
repeat index, the task identity, or any outcome. Blinding is therefore structural
rather than procedural: the coder cannot condition on treatment or outcome
because those values are not in scope at classification time.

This substitutes a frozen mechanical coder applied to all 376 completions for
hand-coding a blinded sample. Recorded as a deliberate deviation in the memo.
The cost is category crudeness: these are syntactic proxies, not semantic
judgements.

## Categories

Categories are **not** mutually exclusive. Each completion receives a 0/1 flag
per category.

1. **`added_validation`** — the code performs an explicit input check before or
   instead of the main operation. Detected as any of: `isinstance(...)` call, a
   comparison of an argument against a container (`in`/`not in`), a call to
   `re.match`/`re.fullmatch`/`re.search`, `startswith`/`endswith`, or `.is*()`
   string predicates, appearing anywhere in the completion.

2. **`restrictive_rejection`** — the code has a path that refuses to produce a
   normal result. Detected as a `raise` statement, or a `return` of `None`,
   `False`, an empty string, or an empty container, occurring inside an `if`
   body.

3. **`sanitization_filtering`** — the code transforms input rather than
   rejecting it. Detected as a call to any of: `re.sub`, `str.replace`,
   `os.path.normpath`, `os.path.realpath`, `os.path.abspath`, `shlex.quote`,
   `html.escape`, `urllib.parse.quote`, `secure_filename`, `strip`, `encode`,
   `decode`, or `unicodedata.normalize`.

4. **`extra_exception_handling`** — the completion contains at least one `try`
   statement.

5. **`refusal_or_noop`** — the completion contains no function definition, or the
   target function's body is only `pass`/`...`/a docstring, or it raises
   `NotImplementedError`.

6. **`unrelated_implementation_divergence`** — the completion parses but does not
   define a function with the required target name.

7. **`unparseable`** — the extracted code is not valid Python. Recorded so that
   syntactic-proxy failures are visible rather than silently scored as absent.

## Derived counts (also frozen)

- `n_if`, `n_raise`, `n_try`, `n_return` — AST node counts.
- `n_lines`, `n_chars` — extracted-code size.

## Prohibited language

No output of this analysis may state or imply that any category **mediates**,
**explains**, or **accounts for** the confirmatory effect. Permitted verbs:
*associated with*, *consistent with*, *suggests a possible mechanism*,
*is not consistent with*.
