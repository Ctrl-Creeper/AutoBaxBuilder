"""Data-flow audit: mechanical proof that Study-1 execution code cannot depend on
S′-side artifacts.

Three independent checks over the three execution-path files (builder, validator,
scorer — the code that runs when Study 1 actually executes):

  1. Static literal scan — no banned artifact name, path fragment, or S′-side
     construct name appears anywhere in the source text (comments included).
  2. Import scan — the AST's imports resolve only to the standard library, numpy,
     the benchmark loader, and Study-1's own modules. No Round-2 or writer-side
     module can enter the import graph.
  3. Runtime trace — the self-test records every file the process opened
     (sys.addaudithook); the audit asserts the trace touches no banned artifact.

The self-test and this audit file are excluded from the static scan by design: they
must name the banned artifacts in order to check for them, and neither runs in the
execution path.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXECUTION_FILES = ("build_study1_packets.py", "validate_study1_submission.py",
                   "score_study1_prevalence.py")

BANNED_LITERALS = [
    "writer_output", "writer_handoff", "ACCEPTED.json", "ACCEPTED_SHA",
    "_KEY_DO_NOT_SHOW_WRITER", "2026-08-26_round2_coder_packets",
    "results_pre_adjudication", "coder1_answers", "coder2_answers",
    "coder1_package", "coder2_package",
    "build_round2", "score_reliability", "align_submissions", "diagnose_disagreements",
    "S_prime", "F1_LIST", "F3_PREAMBLE", "sufficiency_evidence",
]
BANNED_PATTERNS = [r"\bJ2\b", r"\bJ3\b"]  # Study 1 is J1-only; the retired judgements
                                          # may not even be named in execution code
ALLOWED_IMPORTS = {
    # stdlib actually used by the three files
    "__future__", "argparse", "collections", "hashlib", "json", "pathlib", "re",
    "subprocess", "sys", "tempfile", "types",
    # third party
    "numpy",
    # the benchmark loader and Study-1's own modules
    "secodeplt_task_runner", "build_study1_packets",
}

fails: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {msg}")
    if not ok:
        fails.append(msg)


def main() -> None:
    for name in EXECUTION_FILES:
        src = (HERE / name).read_text()
        hits = [lit for lit in BANNED_LITERALS if lit in src]
        hits += [p for p in BANNED_PATTERNS if re.search(p, src)]
        check(not hits, f"{name}: no banned literal or pattern (found {hits or 'none'})")

        tree = ast.parse(src)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        illegal = imported - ALLOWED_IMPORTS
        check(not illegal, f"{name}: imports within the allowlist (illegal: {sorted(illegal) or 'none'})")

    trace_p = HERE / "selftest_open_trace.json"
    check(trace_p.exists(), "runtime open trace exists (self-test must run first)")
    if trace_p.exists():
        trace = json.loads(trace_p.read_text())
        banned_dirs = ["writer_handoff", "2026-08-26_round2_coder_packets", "writer_output"]
        touched = [p for p in trace["opens"] if any(b in p for b in banned_dirs)]
        check(not touched,
              f"runtime trace touches no banned artifact ({len(trace['opens'])} opens)")
        check(trace.get("banned_touched") == [],
              "self-test's own banned-artifact assertion recorded clean")

    print(f"\n{'DATA-FLOW AUDIT PASSED' if not fails else str(len(fails)) + ' FAILURE(S)'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
