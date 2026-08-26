"""Self-test for resubmission identity gate v2.

The positive fixture is exactly the remedy being asked for: correct the 37 flagged
actions, expand the 8 flagged quotations, touch nothing else. Every negative is a
route by which the amendment could be stretched past metadata correction.

Run:  python test_resubmission_identity_gate_v2.py
"""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = HERE / "resubmission_identity_gate_v2.py"
SUB = HERE.parent / "submissions"
TASKS = HERE.parent / "writer_package/tasks"
sys.path.insert(0, str(HERE))
from validate_writer_output import norm, parse_original  # noqa: E402


def prev() -> dict:
    return json.loads((SUB / "writer_output_v2_resubmission1.json").read_text())


def flagged() -> tuple[set, set]:
    msgs = json.loads((SUB / "writer_validator_report_on_resubmission1.json").read_text())["hard_failures"]

    def parse(p):
        return {(g.group(1), int(g.group(2))) for m in msgs if p in m
                for g in [re.match(r"(W\d\d) edit (\d+)", m)] if g}
    return (parse("action is rewritten but no replacement is given"),
            parse("the quoted original is not present in the frozen"))


def positive(p: dict) -> dict:
    """Correct exactly what the validator flagged, and nothing else."""
    d = copy.deepcopy(p)
    fa, fq = flagged()
    for wid, t in d["tasks"].items():
        orig = parse_original((TASKS / f"{wid}.md").read_text())
        for i, e in enumerate(t["edits"], 1):
            if (wid, i) in fa:
                e["action"] = "removed"
                e["replacement"] = ""
            if (wid, i) in fq:
                # complete the abbreviated quotation from the frozen input
                head = re.split(r"\{\.\.\.\}|\.\.\.", e["original"])[0].strip()
                field_text = orig.get(e["field"], "")
                for s in [field_text] + [s.strip() for s in field_text.split("\n")]:
                    if norm(head) and norm(head) in norm(s):
                        e["original"] = s.strip()
                        break
    return d


def run(sub: dict) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(sub, f, ensure_ascii=False)
        path = f.name
    r = subprocess.run([sys.executable, str(GATE), path], capture_output=True, text=True)
    Path(path).unlink()
    return r.returncode, r.stdout + r.stderr


def negatives(p: dict, pos: dict) -> dict[str, dict]:
    out = {}
    fa, fq = flagged()
    fa_wid, fa_i = sorted(fa)[0]
    fq_wid, fq_i = sorted(fq)[0]
    first = sorted(p["tasks"])[0]

    def mut(name, fn):
        d = copy.deepcopy(pos)
        fn(d)
        out[name] = d

    mut("candidate_prose_edited", lambda d: d["tasks"][first]["spec"].update(
        {"description": d["tasks"][first]["spec"]["description"] + " Reworded."}))
    mut("action_changed_without_flag", lambda d: next(
        e.update({"action": "removed", "replacement": ""})
        for w, t in d["tasks"].items() for i, e in enumerate(t["edits"], 1)
        if (w, i) not in fa and e["action"] == "rewritten"))
    mut("action_reversed", lambda d: d["tasks"][fa_wid]["edits"][fa_i - 1].update(
        {"action": "rewritten", "replacement": "invented text"}))
    mut("quotation_substituted", lambda d: d["tasks"][fq_wid]["edits"][fq_i - 1].update(
        {"original": "an entirely different clause not in the input"}))
    mut("quotation_changed_without_flag", lambda d: next(
        e.update({"original": e["original"] + " extra"})
        for w, t in d["tasks"].items() for i, e in enumerate(t["edits"], 1)
        if (w, i) not in fq and (w, i) not in fa))
    mut("field_retargeted", lambda d: d["tasks"][fa_wid]["edits"][fa_i - 1].update({"field": "context"}))
    mut("why_rewritten", lambda d: d["tasks"][fa_wid]["edits"][fa_i - 1].update({"why": "new rationale"}))
    mut("edit_deleted", lambda d: d["tasks"][first]["edits"].pop(0))
    mut("task_removed", lambda d: d["tasks"].pop(first))
    mut("notes_changed", lambda d: d["tasks"][first].update({"notes": "second thoughts"}))
    mut("failure_reinterpreted", lambda d: next(
        t.update({"failure": None}) for t in d["tasks"].values() if t.get("failure")))
    mut("sufficiency_evidence_changed", lambda d: d["tasks"][first].update({"sufficiency_evidence": []}))
    mut("schema_version_changed", lambda d: d.update({"schema_version": "round2-writer-v3"}))
    return out


def main() -> None:
    p = prev()
    pos = positive(p)

    print("positive fixture — flagged actions and quotations corrected, nothing else")
    code, out = run(pos)
    ok = code == 0 and "PASSED" in out
    print(f"  {'ok  ' if ok else 'FAIL'} accepted")
    if not ok:
        print("\n".join(out.splitlines()[:14]))
    failures = 0 if ok else 1

    print("\nunchanged resubmission — the gate permits a no-op; the validator still rejects it")
    code, _ = run(copy.deepcopy(p))
    print(f"  {'ok  ' if code == 0 else 'FAIL'} accepted")
    failures += 0 if code == 0 else 1

    print("\nnegative fixtures — each stretches the amendment one step too far")
    for name, sub in negatives(p, pos).items():
        code, out = run(sub)
        good = code == 1 and "FAILED" in out
        print(f"  {'ok  ' if good else 'FAIL'} {name}")
        if not good:
            failures += 1
            print("        " + "\n        ".join(out.splitlines()[-3:]))

    print(f"\n{'SELF-TEST PASSED' if not failures else str(failures) + ' FAILURES'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
