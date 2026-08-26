"""Self-test for the resubmission identity gate.

The positive fixture is the remedy the writer is actually being asked for: lowercase
the `edits[].field` values and append the missing declarations, touching nothing
else. Each negative changes exactly one further thing, and every one of them is a
route by which validator feedback could otherwise reach the specifications.

Run:  python test_resubmission_identity_gate.py
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = HERE / "resubmission_identity_gate.py"
BASELINE = HERE.parent / "submissions/writer_output_v1_baseline.json"


def load_baseline() -> dict:
    return json.loads(BASELINE.read_text())


def positive(base: dict) -> dict:
    """Casing corrected, missing declarations appended, nothing else touched."""
    d = copy.deepcopy(base)
    for wid, t in d["tasks"].items():
        for e in t["edits"]:
            e["field"] = str(e["field"]).strip().lower()
        t["edits"].append({"field": "description", "action": "rewritten",
                           "original": "synthetic declaration for the self-test",
                           "replacement": "synthetic", "why": "completing provenance"})
    return d


def run(sub: dict) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(sub, f, ensure_ascii=False)
        p = f.name
    r = subprocess.run([sys.executable, str(GATE), p, "--baseline", str(BASELINE)],
                       capture_output=True, text=True)
    Path(p).unlink()
    return r.returncode, r.stdout + r.stderr


def negatives(base: dict, pos: dict) -> dict[str, dict]:
    out = {}

    def mut(name, fn):
        d = copy.deepcopy(pos)
        fn(d)
        out[name] = d

    first = sorted(base["tasks"])[0]
    mut("candidate_prose_edited",
        lambda d: d["tasks"][first]["spec"].update(
            {"description": d["tasks"][first]["spec"]["description"] + " Reworded."}))
    # Target a task whose Raise is actually populated; on a task where it is
    # already empty the mutation is a no-op and would test nothing.
    has_raise = next(w for w in sorted(base["tasks"])
                     if base["tasks"][w]["spec"]["raise"].strip())
    mut("candidate_prose_shortened",
        lambda d: d["tasks"][has_raise]["spec"].update({"raise": ""}))
    mut("task_removed", lambda d: d["tasks"].pop(first))
    mut("task_added", lambda d: d["tasks"].update({"W99": d["tasks"][first]}))
    mut("existing_edit_modified",
        lambda d: d["tasks"][first]["edits"][0].update({"why": "changed rationale"}))
    mut("existing_edit_removed", lambda d: d["tasks"][first]["edits"].pop(0))
    mut("edits_reordered", lambda d: d["tasks"][first]["edits"].reverse())
    mut("notes_changed", lambda d: d["tasks"][first].update({"notes": "second thoughts"}))
    mut("sufficiency_evidence_changed",
        lambda d: d["tasks"][first].update({"sufficiency_evidence": []}))
    mut("failure_reinterpreted", lambda d: next(
        t.update({"failure": None}) for t in d["tasks"].values() if t.get("failure")))
    mut("failure_code_swapped", lambda d: next(
        t["failure"].update({"code": "F5_MATERIAL_DEFECT"})
        for t in d["tasks"].values() if t.get("failure")))
    mut("schema_version_changed", lambda d: d.update({"schema_version": "round2-writer-v2"}))
    mut("writer_id_changed", lambda d: d.update({"writer_id": "someone-else"}))
    mut("unexpected_key", lambda d: d["tasks"][first].update({"reviewer_note": "x"}))
    return out


def main() -> None:
    base = load_baseline()
    pos = positive(base)

    print("positive fixture — casing corrected, declarations appended, nothing else")
    code, out = run(pos)
    ok = code == 0 and "IDENTITY GATE PASSED" in out
    print(f"  {'ok  ' if ok else 'FAIL'} accepted")
    if not ok:
        print(out)
    failures = 0 if ok else 1

    print("\nunchanged resubmission — no casing fix, no appends")
    code, out = run(copy.deepcopy(base))
    ok = code == 0
    print(f"  {'ok  ' if ok else 'FAIL'} accepted (a no-op is inside the allowlist; the writer "
          f"validator is what still rejects it)")
    failures += 0 if ok else 1

    print("\nnegative fixtures — each changes exactly one further thing")
    for name, sub in negatives(base, pos).items():
        code, out = run(sub)
        good = code == 1 and "IDENTITY GATE FAILED" in out
        print(f"  {'ok  ' if good else 'FAIL'} {name}")
        if not good:
            failures += 1
            print("        " + "\n        ".join(out.splitlines()[-3:]))

    print(f"\n{'SELF-TEST PASSED' if not failures else str(failures) + ' FAILURES'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
