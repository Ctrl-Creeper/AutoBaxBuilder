# GAP-3 — environment-dependent oracle materialization (scope report)

**Status.** Formal gap record + outcome-blind scope audit, per the 2026-08-28 ruling.
Discovered during the pre-coding packet audit, **before any coder exposure and before any
baseline outcome exists**. No handling rule is chosen here; no protocol, selection, builder
extraction semantics, or packet was modified; no packets were rebuilt.

## 1. The gap

Selected task P32 (source index **864**, `filtered_system_command`, CWE-77): the benchmark's
own testcase source computes expected values by **executing commands at extraction time**
(`os.popen(...)` calls, including a directory listing and a read of `/etc/passwd`). The
case's expected behaviour *b* therefore depends on the execution environment and time, and
the frozen source→case byte-reproduction invariant cannot hold: the packet audit's
from-source re-rendering check failed when re-extraction happened minutes after the build
(embedded timestamps changed). The extraction interface itself is the frozen Round-2 rule
(subprocess execution of setup+testcases); Study 1's 90 tasks happened to contain no such
record, so the identical check passed there.

Consequence recorded, not resolved: the materialized packet content embedded local machine
data (`/etc/passwd` contents, temp-dir listing) in a coder-visible expected-behaviour cell.

## 2. Quarantine (ruling C)

The failed build is preserved unfrozen and uncommitted, marked
`QUARANTINED_PREVALIDATION_BUILD — NOT FOR CODING / NOT FOR RELEASE`.
No coder has seen any file in it. Hashes (contents not copied into this report):

| artifact | sha256 |
|---|---|
| quarantined build tree (188 files, sorted relpath+sha list) | `3ea64b313dc8be2d13c37d862160d146eddea7bd2904ccb33607e3137a711b53` |
| sealed key | `104b96e03c85127173009860aa9b92477d9420c9c90cd5eefa58b163f9a4ef2f` |
| packet fingerprint (both runs) | `e20d542c16922138a41f98f6c7ff86977ba01c6d69ac3bf32b9c8f87c3d4485c` |
| quarantine marker | `de0fac0a514c361b6ddf08bf2469279437b335dca3bfddfd0c62d76e47b41e43` |

The 20 non-GAP audit checks passed on this build (selection identity, seed disjointness,
payload equality run1=run2, permutation reproduction, key isolation, blank-template
validation); they are facts about the quarantined object, not a freeze.

## 3. FAIL-2 audit amendment (ruling A) — implemented

`audit_baseline_packets.py` amended before any freeze of that file: the lexical
banned-token scan now covers researcher-generated material only (framing, instructions,
templates, fingerprints, filenames); benchmark-derived S blocks and case cells are exempt.
Compensating mechanical provenance check added: every task file must byte-decompose into
(fixed template) + (shipped get_prompt output) + (case cells whose inputs equal the frozen
extractor's fresh output), so nothing else can occupy the exemption. No per-hit manual
exception mechanism exists. On the quarantined build the amended audit yields 21/22 — the
single remaining failure is this GAP's byte-reproduction check, as expected.

## 4. Outcome-blind scope audit (ruling D) — is P32 isolated?

Method (`gap3_scope_audit.py`, results `gap3_scope_results.json`): over all 764 frame
tasks, (a) static AST scan of setup+testcases source for dependency classes; (b) the frozen
extraction run twice per task in separate subprocesses under different `PYTHONHASHSEED`,
outputs hashed for byte-equality and discarded — no oracle value stored, read, or
classified; no Definition-D judgement exists or was computed.

**Answer: not isolated — a systematic exposure class of the frozen extraction interface.**

| dependency class (static, source mechanics) | frame (764) | in drawn 90 |
|---|---|---|
| **proc_exec** (process execution at extraction: `os.popen`/`os.system`/`subprocess`) | **20** (contiguous family 855–872, plus 1340, 1346, 1347) | **3 — indices 862, 863, 864** |
| fs_read (filesystem reads at extraction) | 20 | 1 (864, overlapping) |
| network (network-capable imports in extraction source; over-inclusive surface indicator — import ≠ extraction-time I/O) | 125 | 13 |
| randomness | 1 | 0 |
| time_dep / env_dep / unordered_repr (static) | 0 | 0 |

Dynamic probe: 763/764 byte-stable, 0 extraction errors, 1 unstable — **index 915**
(hash-seed-sensitive representation; no static class caught it; not in the drawn 90).

**Method caveat, stated so the numbers are not over-read:** the dynamic double-extraction
runs nearly simultaneously on one machine, so it detects hash-seed instability but NOT
time/environment dependence — index 864 itself probes "stable" here while demonstrably
breaking at minutes-scale in the packet audit. The by-construction exposure measure is the
static proc_exec class (oracle materialized from the environment regardless of whether two
close-in-time runs happen to agree); 862 and 863 passed the build audit's byte check at
~2-minute separation but sit in the same class as 864.

## 5. Protocol handling branch: **UNDEFINED**

The frozen protocol (`548addbd…`) was checked for a handling branch covering "a selected
task cannot yield a stable, mechanically reproducible case object". None exists: §4 fixes
cases as immutable components and §0 inherits the Round-2 mechanical extraction rule, both
silently assuming a stable case object; no clause defines what happens when the assumption
fails. **The handling of GAP-3 tasks is UNDEFINED in the frozen protocol.** Per the ruling,
no handling rule (snapshot-freezing, exclusion, ineligibility, UR, replacement, redraw) is
chosen or designed here; all remain open for adjudication.

## 6. State at stop

Selection manifest `b194696c…` unchanged and frozen; no packets frozen; no coder session
started; no eligibility derived. Awaiting adjudication of GAP-3 handling.
