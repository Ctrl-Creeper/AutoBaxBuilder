# GAP-8 - Historical Run-1 terminal artifact vs formal Run-2 constructive path

Date: 2026-09-07 (Asia/Taipei)

Status: frozen static scorer-contract audit. No scorer execution, scoring calculation, code
change, task-level classification inspection, or substantive candidate inspection occurred in
this gate.

Audit base: commit `bb2fdd27a0c80dcbdda4a7950875ccf56801b1c0`.

## Frozen evidence and pins

| Evidence | SHA256 / frozen status |
|---|---|
| Study-3 protocol | `548addbd9277dbe901b8e1e599fdf3a6d4ef97e286610dbecc40bf1f5f5f81d7` |
| Current `score_study3.py` | `2425c8d10938b9828a2bca625366483408ec69e28eb2a412e6db809bb48dd8db` |
| Amendment 3 | `4a599951674d1f07109a6838e973e9f92e1db9e1c5ff6f7aabb2a80695ac35a6` |
| GAP-5 Interpretation Note 2 | `08f6298a3f3a1741e02c6f46fd394e4f7b97d071b4150f5fe8395dc1f7d93357` |
| GAP-6 contract audit | `a5ac01698990a04a6a9cd6d67dd6bc54d851f19de0a951172c91d7ea2f9a167c` |
| GAP-6 repair record | `a52fc7ee3704ae265dfc37dac860487969c848f91f3a43ba5f4146d1675b8dca` |
| Historical Run-1 gate artifact | `357e241ea030ee598f8a091a4f9dacc2947f1f5de9249a9f1ce189cecf19f4c4`; verdict `UNREPAIRABLE_FIRST_SUBMISSION` |
| Run-2 terminal record | `ee64173d1479c8a143f9acd9eedc9466c8181f3c618bd29f84ea8367c3ae4545`; status `ACCEPT_FIRST_RUN2` |
| Authoritative Run-2 accepted artifact | `f2b0e73ab1d8b5efcb22bb53c2b8d026446994992195d9b55b483d8de593b49e` |
| Frozen DS derivation | `3377d187c2c37177f37e1c9b5d648b34468d10bd4239404b971888c835e4efe7` |
| Frozen VO derivation | `cd2cc35b269a1d27d9093462685eae09ace6dc07d9fec95002f9cba55d3c0060` |

The audit used only source, frozen manifests, terminal statuses, and provenance. It did not read
task-level DS/VO/UR status, verifier judgements or quotes, writer obstruction declarations, or
candidate substance. `results_study3.json` does not exist.

## Offending frozen branch

`score_study3.py:158-185` implements the GAP-5 terminal-state resolver. Lines 162-164 hard-stop
whenever both `ds_derivation.json` and
`writer_handoff/GATE_UNREPAIRABLE_FROZEN.json` exist. This resolver is based only on file
existence and does not consult the later frozen GAP-6 disposition or the Run-2 terminal record.

The branch was correct for the two terminal states that GAP-5 defined before any writer output:
an accepted constructive path represented by the DS derivation, or a formal procedure-invalid
path represented by the unrepairable gate. It became interface-incomplete only after GAP-6 kept
the Run-1 gate as historical provenance and authorized a fresh repaired Run 2.

## G8 rulings

### G8-1 - PASS

The XOR was expressly introduced to distinguish the valid constructive path from the formal
procedure-invalid constructive path. Interpretation Note 2 lines 46-54 defines those two paths;
lines 68-72 then requires exactly one of the DS derivation or the hash-verified unrepairable gate.
The scorer comment at lines 158-159 repeats that contract.

### G8-2 - PASS

GAP-6 formally marks Run 1 `WRITER_INSTRUMENT_CONTRACT_FAILURE`. The contract audit states that
the mechanical Run-1 terminal state remains a true retained execution result but is not
construct-level evidence. The repair record is stronger and explicit: Run 1 enters no DS/VO/UR
identification result. Its gate artifact therefore remains evidence about the historical
instrument execution, not a formal procedure-invalid input to the repaired constructive path.

### G8-3 - PASS

The Run-2 terminal record freezes `ACCEPT_FIRST_RUN2`. GAP-7 fixes a single zero-argument loader
to the exact Run-2 accepted artifact and manifest, with no path parameter, scan, or fallback.
That input was used to build and freeze the S-prime verification path, after which the frozen DS
derivation was mechanically produced. The existence and frozen provenance of those artifacts,
not their task-level outcomes, establish a valid formal constructive path.

### G8-4 - PASS

The current Run-1 gate artifact serves historical/provenance retention only. "Not superseded"
in the Run-2 terminal record means the Run-1 execution fact remains reportable; it does not
restore that contract-failure run to the formal classification path. GAP-6 explicitly excludes
it from DS/VO/UR identification, and GAP-7 states that neither old Run-1 path can be a
constructive input.

### G8-5 - PASS

A terminal/provenance-only amendment can leave all substantive scoring behavior unchanged. The
resolver runs before the already-separated pure scoring functions and supplies the same accepted
branch objects: mechanically mapped DS input, an empty `procedure_invalid` set, and the fixed
Run-2 writer loader. The VO artifact continues to enter at the existing interface.

The following current function-source hashes are the byte-identity boundary for any amendment:

| Function | SHA256 |
|---|---|
| `cp_interval` | `7525022292ad3693b063b5b9a814a3705330d1c3abc3f130ffd0844dd52bcf4a` |
| `map_ds_to_baseline` | `0d7659e562c868dd217f9129a9c568d9f9444acbb95e2d393b917feeb3456b74` |
| `classify` | `d7dd69b6e933f229904c136737c470a68253a823aa2a791331322f3e3a0f4aff` |
| `score` | `51e2e4cdb394a8a07506309bd9c1cf0bdb82b5182f8da3979345ef88fc3582e6` |

These functions, their fixtures, and their behavior must remain byte-identical or
behavior-identical as applicable. The amendment may not alter classification, DS/VO/UR rules,
denominator handling, L0 equations, endpoint intervals, L2 sensitivity, the DS/VO overlap
hard-stop, VO handling, or procedure-invalid semantics.

### G8-6 - PASS

A fixed, zero-argument, no-fallback provenance resolver can implement the bounded interface. It
must mechanically pin all of the following before returning the formal accepted path:

1. The exact historical Run-1 gate hash and `UNREPAIRABLE_FIRST_SUBMISSION` status.
2. The frozen GAP-6 audit/repair disposition that classifies Run 1 as an instrument-contract
   failure outside DS/VO/UR identification.
3. The exact Run-2 terminal manifest/record, `ACCEPT_FIRST_RUN2` status, and sole accepted
   artifact hash.
4. The frozen DS manifest and exact derivation hash.

The resolver may then allow the exact historical Run-1 artifact to coexist with the formal
Run-2 DS path. It may not accept arguments, scan for artifacts, select the newest file, use an
existence-only fallback, infer a path from task outcomes, or treat any unpinned artifact as
formal. A missing, mismatched, or contradictory pin remains a HARD STOP.

The existing `score(..., procedure_invalid=...)` contract and its formal procedure-invalid
routing remain unchanged. No new procedure-invalid definition or terminal artifact is created by
this amendment; in particular, the historical Run-1 gate may never be reinterpreted as the
current formal procedure-invalid terminal.

## Authorized amendment boundary

The only authorized follow-up is a bounded scorer provenance amendment that replaces the stale
existence-only terminal resolution in `main()` with the fixed resolver described above. Allowed
changes are limited to:

- fixed provenance constants and a zero-argument resolver;
- exact hash/status checks for the already frozen Run-1, GAP-6, Run-2, and DS artifacts;
- the minimal `main()` wiring needed to consume the resolved terminal state;
- provenance-only metadata and focused fixtures proving refusal on every mismatch and proving
  substantive function source/behavior identity.

Forbidden changes include all substantive scoring functions or formulas, classifications,
denominators, DS/VO handling, overlap behavior, procedure-invalid meaning, statistical output,
sensitivity definitions, task selection, and any outcome-conditioned fallback.

## Outcome firewall and execution status

No scorer or derivation was run in this gate. No L0/L1/L2 quantity was computed. No Run-1
artifact was deleted, moved, renamed, or modified. No frozen source was changed. The prior scorer
hard-stop produced no result artifact and remains intact. There was no execution deviation.

## Final ruling

`BOUNDED_PROVENANCE_AMENDMENT_AUTHORIZED`

G8-1 through G8-6 are all PASS. This ruling authorizes a later separately gated patch only within
the boundary above; it does not implement that patch or authorize final scoring.
