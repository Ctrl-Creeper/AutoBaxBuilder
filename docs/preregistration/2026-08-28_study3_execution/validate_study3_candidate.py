"""Study 3 — mechanical validation of the writer's candidate output.

Checks ONLY the mechanical invariants of constraint set C (protocol §4) plus schema and
completeness. It never judges whether a candidate succeeds — capability preservation and
safety underdetermination are established only by the blinded J1 evidence, downstream.

Invariants checked, nothing more:
  - schema: exact template shape; every eligible task present, none extra;
  - a candidate ALWAYS ships: the five prose fields are non-empty strings even when a
    failure is declared (writer failure never drops a task);
  - security_policy is null (removed) or a non-empty string (kept/rewritten);
  - parameter mentions: every parameter of the original def line appears as an identifier
    token in the candidate's arguments field (protocol §4's mechanical check);
  - failure is null or {code ∈ F1..F5, at_case, detail, quotes[]} with each quote locating
    (normalised substring) in the writer's own task file — the structured obstruction
    declaration with quotations that §5 requires;
  - edits[] entries have exactly {field, original, action, replacement, why} with action
    in {removed, rewritten}.

Usage: validate_study3_candidate.py <writer_output.json> [--json OUT]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from study3_pins import EDITABLE_FIELDS, FAILURE_CODES, SCHEMA_WRITER, norm

HERE = Path(__file__).resolve().parent
PKG = HERE / "writer_handoff" / "writer_package"

SPEC_KEYS = set(EDITABLE_FIELDS) | {"security_policy"}
TASK_KEYS = {"spec", "edits", "sufficiency_evidence", "failure", "notes"}
EDIT_KEYS = {"field", "original", "action", "replacement", "why"}
FAILURE_KEYS = {"code", "at_case", "detail", "quotes"}

problems: list[str] = []


def bad(msg: str) -> None:
    problems.append(msg)


def check_task(wid: str, t: dict, task_md: str, params: list[str]) -> None:
    if set(t) != TASK_KEYS:
        bad(f"{wid}: task keys {sorted(t)} != {sorted(TASK_KEYS)}")
        return
    spec = t["spec"]
    if not isinstance(spec, dict) or set(spec) != SPEC_KEYS:
        bad(f"{wid}: spec keys {sorted(spec) if isinstance(spec, dict) else '?'} "
            f"!= {sorted(SPEC_KEYS)}")
        return
    for f in EDITABLE_FIELDS:
        if not (isinstance(spec[f], str) and spec[f].strip()):
            bad(f"{wid}: spec.{f} empty — a candidate always ships, failure or not")
    sp = spec["security_policy"]
    if not (sp is None or (isinstance(sp, str) and sp.strip())):
        bad(f"{wid}: security_policy must be null (removed) or a non-empty string")

    if isinstance(spec.get("arguments"), str):
        for p in params:
            if not re.search(rf"\b{re.escape(p)}\b", spec["arguments"]):
                bad(f"{wid}: parameter {p!r} no longer mentioned in arguments — "
                    "constraint C violated (the interface must stay the same task)")

    if not isinstance(t["edits"], list):
        bad(f"{wid}: edits is not a list")
    else:
        for e in t["edits"]:
            if not isinstance(e, dict) or set(e) != EDIT_KEYS:
                bad(f"{wid}: an edits entry has keys "
                    f"{sorted(e) if isinstance(e, dict) else '?'} != {sorted(EDIT_KEYS)}")
            elif e["action"] not in ("removed", "rewritten"):
                bad(f"{wid}: edits action {e['action']!r} not in removed/rewritten")

    fail = t["failure"]
    if fail is not None:
        if not isinstance(fail, dict) or set(fail) != FAILURE_KEYS:
            bad(f"{wid}: failure keys {sorted(fail) if isinstance(fail, dict) else '?'} "
                f"!= {sorted(FAILURE_KEYS)}")
        else:
            if fail["code"] not in FAILURE_CODES:
                bad(f"{wid}: failure code {fail['code']!r} outside the fixed taxonomy")
            if not (isinstance(fail["quotes"], list) and fail["quotes"]):
                bad(f"{wid}: failure declaration without quotations — "
                    "obstruction claims require verbatim quotes")
            else:
                for q in fail["quotes"]:
                    if not isinstance(q, str) or norm(q) not in norm(task_md):
                        bad(f"{wid}: failure quote does not locate in the task file")

    if not isinstance(t["notes"], str):
        bad(f"{wid}: notes is not a string")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("submission", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()

    tmpl = json.loads((PKG / "output_template.json").read_text())
    sub = json.loads(a.submission.read_text())

    if sub.get("schema_version") != SCHEMA_WRITER:
        bad(f"schema_version {sub.get('schema_version')!r} != {SCHEMA_WRITER!r}")
    if not (sub.get("writer_id") or "").strip():
        bad("writer_id is empty")
    tasks = sub.get("tasks")
    if not isinstance(tasks, dict):
        bad("tasks missing or not an object")
        tasks = {}
    missing = sorted(set(tmpl["tasks"]) - set(tasks))
    unknown = sorted(set(tasks) - set(tmpl["tasks"]))
    if missing:
        bad(f"{len(missing)} eligible task(s) absent — no task may be dropped: {missing[:6]}")
    if unknown:
        bad(f"unknown task ids: {unknown[:6]}")

    key = json.loads((HERE / "writer_handoff/sealed/_KEY_DO_NOT_SHOW_WRITER.json").read_text())
    from secodeplt_task_runner import load  # noqa: E402  (benchmark loader only)
    records = {r["index"]: r for r in load(only_stdlib=False)}
    from study3_pins import param_names

    for wid in sorted(set(tmpl["tasks"]) & set(tasks)):
        task_md = (PKG / "tasks" / f"{wid}.md").read_text()
        params = param_names(records[key["tasks"][wid]["index"]])
        check_task(wid, tasks[wid], task_md, params)

    for p in problems[:30]:
        print(f"  PROBLEM {p}")
    if len(problems) > 30:
        print(f"  … and {len(problems) - 30} more")
    res = {"submission": str(a.submission), "problems": problems, "accepted": not problems,
           "n_tasks": len(tasks),
           "failure_declarations": sum(1 for t in tasks.values()
                                       if isinstance(t, dict) and t.get("failure"))}
    if not problems:
        res["submission_sha256"] = hashlib.sha256(a.submission.read_bytes()).hexdigest()
        print(f"\nMECHANICAL INVARIANTS OK — {res['n_tasks']} candidates, "
              f"{res['failure_declarations']} failure declaration(s) recorded (not judged)")
        print(f"submission sha256: {res['submission_sha256']}")
    else:
        print(f"\nNOT ACCEPTED — {len(problems)} problem(s); resubmission gates as in Round 2")
    if a.json:
        a.json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
