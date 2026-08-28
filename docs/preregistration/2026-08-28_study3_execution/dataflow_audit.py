"""Study 3 — data-flow audit: mechanical proof of the frozen information boundaries.

What must be impossible, and how each impossibility is shown:

  - Study-1 prevalence/results and case-level judgements cannot enter selection, baseline
    packet building, eligibility, writer handoff, S′/DS/VO derivation, or scoring: no
    execution file names a Study-1 result/submission/sealed artifact (static literal scan),
    imports only allowlisted modules (AST scan — `build_study1_packets` is allowed CODE, it
    defines the frozen packet machinery and reads nothing at import), and the self-test's
    runtime open-trace touches no such artifact.
  - Round-2 J3 (and J2) enter no execution path: the tokens may not even appear in
    execution code; no Round-2 submission/result artifact may be named or opened.
  - Writer artifacts cannot reach the stages that must be blind to them: per-file bans on
    the writer-output literals for the selection tool, baseline builder, submission
    validator, eligibility derivation, DS derivation, and VO derivation. (The S′ builder
    and the scorer read the frozen study3 writer file by design — the builder to render
    candidates, the scorer for the §7 descriptive distribution only.)
  - The selection tool additionally names no benchmark loader and no outcome artifact of
    any kind: its only inputs are the frozen protocol and frame.

The self-test and this audit are excluded from the static scan by design: they must name
banned artifacts to check for them, and neither runs in the execution path.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

EXECUTION_FILES = (
    "study3_pins.py", "select_study3_sample.py", "packet_build.py",
    "build_study3_baseline_packets.py", "validate_study3_submission.py",
    "derive_eligibility.py", "build_study3_writer_handoff.py",
    "validate_study3_candidate.py", "build_study3_sprime_packets.py",
    "derive_ds.py", "vo_certificates.py", "score_study3.py",
)

# banned in EVERY execution file: Study-1 data artifacts, Round-2 coding artifacts,
# the Round-2 writer corpus, and the retired judgement names
BANNED_EVERYWHERE = [
    "results_study1_prevalence", "answers_FROZEN", "scoring_console_output",
    "packet_audit_report", "study1_execution/sealed", "study1_execution/submissions",
    "2026-08-26_round2_coder_packets", "coder1_answers", "coder2_answers",
    "coder1_package", "coder2_package", "align_submissions", "score_reliability",
    "writer_output_ACCEPTED", "writer_output_v1", "writer_output_v2",
    "2026-08-25_writer_handoff",
    "round2_selection.json", "round2_sampling_frame",
]
BANNED_PATTERNS = [r"\bJ2\b", r"\bJ3\b"]

# study3 writer artifacts: banned in the files that must be blind to the writer
WRITER_LITERALS = ["study3_writer", "writer_handoff", "SHA256SUMS_WRITER"]
WRITER_BLIND_FILES = ("select_study3_sample.py", "packet_build.py",
                      "build_study3_baseline_packets.py", "validate_study3_submission.py",
                      "derive_eligibility.py", "derive_ds.py", "vo_certificates.py",
                      "study3_pins.py")

# the selection tool reads the frozen protocol + frame and NOTHING else
SELECTION_EXTRA_BANS = ["secodeplt_task_runner", "eligibility", "ds_derivation",
                        "vo_certificates", "results_study3", "baseline", "sprime"]

ALLOWED_IMPORTS = {
    "__future__", "argparse", "collections", "hashlib", "inspect", "json", "pathlib",
    "re", "subprocess", "sys", "tempfile", "types",
    "numpy", "scipy",
    "secodeplt_task_runner", "build_study1_packets",
    "study3_pins", "select_study3_sample", "packet_build",
}
# the selection tool's import set is far tighter
SELECTION_ALLOWED = {"__future__", "argparse", "hashlib", "json", "pathlib", "sys",
                     "numpy", "study3_pins"}

fails: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {msg}")
    if not ok:
        fails.append(msg)


def imports_of(src: str) -> set[str]:
    out = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            out |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module.split(".")[0])
    return out


def main() -> None:
    for name in EXECUTION_FILES:
        src = (HERE / name).read_text()
        hits = [lit for lit in BANNED_EVERYWHERE if lit in src]
        hits += [p for p in BANNED_PATTERNS if re.search(p, src)]
        if name in WRITER_BLIND_FILES:
            hits += [lit for lit in WRITER_LITERALS if lit in src]
        if name == "select_study3_sample.py":
            hits += [lit for lit in SELECTION_EXTRA_BANS if lit in src]
        check(not hits, f"{name}: no banned literal or pattern (found {hits or 'none'})")

        allowed = SELECTION_ALLOWED if name == "select_study3_sample.py" else ALLOWED_IMPORTS
        illegal = imports_of(src) - allowed
        check(not illegal,
              f"{name}: imports within the allowlist (illegal: {sorted(illegal) or 'none'})")

    trace_p = HERE / "selftest_open_trace.json"
    check(trace_p.exists(), "runtime open trace exists (self-test must run first)")
    if trace_p.exists():
        trace = json.loads(trace_p.read_text())
        banned_dirs = ["2026-08-27_study1_execution/results",
                       "2026-08-27_study1_execution/submissions",
                       "2026-08-27_study1_execution/sealed",
                       "2026-08-25_writer_handoff", "2026-08-26_round2_coder_packets",
                       "results_study1_prevalence", "round2_selection.json"]
        touched = [p for p in trace["opens"] if any(b in p for b in banned_dirs)]
        check(not touched,
              f"runtime trace touches no banned artifact ({len(trace['opens'])} opens)")
        check(trace.get("banned_touched") == [],
              "self-test's own banned-artifact assertion recorded clean")

    print(f"\n{'DATA-FLOW AUDIT PASSED' if not fails else str(len(fails)) + ' FAILURE(S)'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
