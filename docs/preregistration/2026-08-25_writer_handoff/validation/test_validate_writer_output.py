"""Self-test for the writer-output validator.

Builds one synthetic submission that must be ACCEPTED, then derives a negative
fixture for each hard invariant by mutating exactly one thing.

The positive fixture is deliberately a *poor* rewrite: it copies the original
prose through unchanged. That is the point. The validator must accept it, because
whether a candidate really settles or opens anything is the construct the blinded
coding runs measure, and a validator that rejected it would be adjudicating.

Run:  python test_validate_writer_output.py
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent / "writer_package"
VALIDATOR = HERE / "validate_writer_output.py"
sys.path.insert(0, str(HERE))
from validate_writer_output import EDITABLE, SCHEMA_VERSION, parse_original  # noqa: E402


def positive() -> dict:
    """A submission that satisfies every procedural invariant."""
    tasks = {}
    for p in sorted((PKG / "tasks").glob("W*.md")):
        orig = parse_original(p.read_text())
        spec = {f: orig.get(f, "") for f in EDITABLE}
        edits, failure = [], None
        # Exercise the edit-provenance path on a slice of the tasks: drop the
        # Raise field wholesale and declare it.
        if int(p.stem[1:]) % 7 == 0 and orig.get("raise", "").strip():
            edits.append({"field": "raise", "original": orig["raise"], "action": "removed",
                          "replacement": "", "why": "declared removal exercising provenance"})
            spec["raise"] = ""
        if int(p.stem[1:]) % 23 == 0:
            failure = {"code": "F2_SIGNATURE_CARRIER", "at_case": "B1", "detail": "synthetic"}
        tasks[p.stem] = {"spec": spec, "edits": edits,
                         "sufficiency_evidence": [{"case": "A1", "sentence": spec["description"][:60]}],
                         "failure": failure, "notes": ""}
    return {"schema_version": SCHEMA_VERSION, "writer_id": "fixture", "tasks": tasks}


def run(sub: dict, pkg: Path = PKG) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(sub, f)
        path = f.name
    p = subprocess.run([sys.executable, str(VALIDATOR), path, "--package", str(pkg)],
                       capture_output=True, text=True)
    Path(path).unlink()
    return p.returncode, p.stdout + p.stderr


def negatives(base: dict) -> dict[str, dict]:
    out = {}

    def mut(name, fn):
        d = copy.deepcopy(base)
        fn(d)
        out[name] = d

    mut("missing_task", lambda d: d["tasks"].pop("W05"))
    mut("unknown_task_id", lambda d: d["tasks"].update({"W99": d["tasks"]["W01"]}))
    mut("security_policy_in_spec",
        lambda d: d["tasks"]["W01"]["spec"].update({"security_policy": "leaked"}))
    mut("non_editable_smuggled",
        lambda d: d["tasks"]["W01"]["spec"].update({"signature": "def f(): ..."}))
    mut("missing_key_not_defaulted", lambda d: d["tasks"]["W02"].pop("notes"))
    mut("untraceable_edit_original",
        lambda d: d["tasks"]["W01"]["edits"].append(
            {"field": "description", "original": "a clause that was never in the original",
             "action": "removed", "replacement": "", "why": "x"}))
    mut("undeclared_removal",
        lambda d: d["tasks"]["W01"]["spec"].update({"description": ""}))
    mut("replacement_absent_from_candidate",
        lambda d: d["tasks"]["W01"]["edits"].append(
            {"field": "description", "original": d["tasks"]["W01"]["spec"]["description"][:30],
             "action": "rewritten", "replacement": "text nowhere in the candidate", "why": "x"}))
    mut("bad_failure_code",
        lambda d: d["tasks"]["W01"].update(
            {"failure": {"code": "F9_INVENTED", "at_case": "B1", "detail": "x"}}))
    mut("failure_with_empty_candidate",
        lambda d: d["tasks"]["W03"].update(
            {"failure": {"code": "F1_LIST_COUPLING", "at_case": "B1", "detail": "x"},
             "spec": {f: "" for f in EDITABLE},
             "edits": [{"field": f, "original": parse_original((PKG / "tasks/W03.md").read_text()).get(f, ""),
                        "action": "removed", "replacement": "", "why": "x"}
                       for f in EDITABLE if parse_original((PKG / "tasks/W03.md").read_text()).get(f, "").strip()]}))
    mut("coder_vocabulary",
        lambda d: d["tasks"]["W01"].update({"notes": "this one is clearly INSEPARABLE"}))
    mut("schema_version_mismatch", lambda d: d.update({"schema_version": "round1-writer-v0"}))
    mut("empty_writer_id", lambda d: d.update({"writer_id": ""}))
    return out


def main() -> None:
    print("positive fixture (a deliberately poor rewrite: prose copied through)")
    code, out = run(positive())
    ok = code == 0 and "ACCEPTED" in out
    print(f"  {'ok  ' if ok else 'FAIL'} accepted, and no semantic judgement was made")
    if not ok:
        print(out)
    failures = 0 if ok else 1

    print("\nnegative fixtures — each mutates exactly one thing")
    for name, sub in negatives(positive()).items():
        pkg = PKG
        code, out = run(sub, pkg)
        good = code == 1 and "NOT ACCEPTED" in out
        print(f"  {'ok  ' if good else 'FAIL'} {name}")
        if not good:
            failures += 1
            print("        " + "\n        ".join(out.splitlines()[-4:]))

    print("\ntampered package — non-editable material altered after freezing")
    with tempfile.TemporaryDirectory() as t:
        clone = Path(t) / "writer_package"
        subprocess.run(["cp", "-R", str(PKG), str(clone)], check=True)
        f = clone / "tasks" / "W01.md"
        f.write_text(f.read_text().replace("**Signature:** `def ", "**Signature:** `def tampered_"))
        code, out = run(positive(), clone)
        good = code == 1 and "frozen manifest" in out
        print(f"  {'ok  ' if good else 'FAIL'} package_integrity")
        if not good:
            failures += 1

    print(f"\n{'SELF-TEST PASSED' if not failures else str(failures) + ' FAILURES'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
