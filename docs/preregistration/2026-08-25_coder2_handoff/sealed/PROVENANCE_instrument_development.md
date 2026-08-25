# Instrument-development provenance: what changed between `fcf1120` and `84ec0d47`

**Sealed.** Not part of the coder package. Reading this before coding would reveal the study's
direction, the first coder's counts, and the answer to J3 on several tasks.

This records one change, made while drafting the protocol and before any second coding, so that the
first coder's result and the frozen protocol can be read against each other later without
reconstruction.

## What happened

The first-coder round (`fcf1120`) applied a determination judgement without ever defining what the
specification consisted of. In practice it reasoned over the prose fields only.

While writing Definition D for the protocol, the phrase "reads only *S*" made the omission visible:
the artefact the implementing model is actually shown is the prose fields **plus the setup/preamble
code plus the function signature**, per the benchmark's own prompt builder, which emits the prose
fields and then `Setup Code:` verbatim and presents the signature through `code_before`.

Defining *S* that way was adopted in `84ec0d47` §1.

## What it cost

Under the corrected definition, six of the ten tasks recorded separable at `fcf1120` have a setup
global whose name or value states the rule:

| task index | setup global |
|---|---|
| 666 | `ALLOWED_CDN_DOMAINS` |
| 681 | `APPROVED_API_DOMAINS`, `ALLOWED_ENDPOINTS` |
| 643 | `ALLOWED_DOMAINS` |
| 1083 | `ALLOWED_REDIRECT_DOMAINS` |
| 1067 | `ALLOWED_FIELDS` |
| 434 | `TRUSTED_DEVICE_SIGNATURES`, keyed by device id alongside a signature parameter |

So at most four of twelve remain separable on the first coder's own reasoning. The four with no
obligation-bearing global are 816, 893, 813, 1350.

## What was deliberately not done

`fcf1120` was **not** edited. The first coder's classifications stand as recorded, made under the
undefined *S*. The second coder codes against `84ec0d47`, where *S* is defined. The two sets are
compared as they stand.

The gap between them is therefore expected, and its size is a measurement in its own right: it is
how much work the undefined *S* was silently doing. Reconciling the two by revising the earlier
record would destroy that measurement.

## Why this is a result and not only an error

It completes the enumeration of where a security obligation can be carried. Only the first of the
three is removable under the transformation rule:

1. **Propositional** — a clause in the prose. Removable.
2. **Structural, in the interface** — a required parameter whose only role is the security decision.
   Not removable; the signature is immutable.
3. **Structural, in the preamble** — a global supplied by the setup code whose name or value states
   the rule. Not removable; the setup is immutable.

Where the obligation is structural, a security-underdetermined specification does not exist to be
constructed, so an ablation-based design is ill-posed for that task rather than merely expensive.
This is the claim the second coder's J3 tests independently, without being told it exists.
