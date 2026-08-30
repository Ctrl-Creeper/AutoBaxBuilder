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

Amendment 3 (format extension only; no check weakened, none removed, messages unchanged):
every problem also carries a machine-readable issue code from the frozen enumeration in
AMENDMENT_3_study3_native_resubmission_gate.md, the report always records the raw-byte
submission_sha256, and an unparseable submission yields INVALID_SERIALIZATION instead of
a traceback. The resubmission gate consumes `issues` and `submission_sha256`; it never
parses the human-readable strings.

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
issues: list[dict] = []


def bad(msg: str, code: str, task: str | None = None) -> None:
    problems.append(msg)
    issues.append({"code": code, "task": task, "message": msg})


def check_task(wid: str, t: dict, task_md: str, params: list[str]) -> None:
    if set(t) != TASK_KEYS:
        bad(f"{wid}: task keys {sorted(t)} != {sorted(TASK_KEYS)}",
            "TASK_SHAPE_ERROR", wid)
        return
    spec = t["spec"]
    if not isinstance(spec, dict) or set(spec) != SPEC_KEYS:
        bad(f"{wid}: spec keys {sorted(spec) if isinstance(spec, dict) else '?'} "
            f"!= {sorted(SPEC_KEYS)}", "CANDIDATE_SCHEMA_ERROR", wid)
        return
    for f in EDITABLE_FIELDS:
        if not (isinstance(spec[f], str) and spec[f].strip()):
            bad(f"{wid}: spec.{f} empty — a candidate always ships, failure or not",
                "EMPTY_CANDIDATE_FIELD", wid)
    sp = spec["security_policy"]
    if not (sp is None or (isinstance(sp, str) and sp.strip())):
        bad(f"{wid}: security_policy must be null (removed) or a non-empty string",
            "SECURITY_POLICY_INVALID", wid)

    if isinstance(spec.get("arguments"), str):
        for p in params:
            if not re.search(rf"\b{re.escape(p)}\b", spec["arguments"]):
                bad(f"{wid}: parameter {p!r} no longer mentioned in arguments — "
                    "constraint C violated (the interface must stay the same task)",
                    "IMMUTABLE_COMPONENT_CHANGED", wid)

    if not isinstance(t["edits"], list):
        bad(f"{wid}: edits is not a list", "PROVENANCE_SHAPE_ERROR", wid)
    else:
        for e in t["edits"]:
            if not isinstance(e, dict) or set(e) != EDIT_KEYS:
                bad(f"{wid}: an edits entry has keys "
                    f"{sorted(e) if isinstance(e, dict) else '?'} != {sorted(EDIT_KEYS)}",
                    "PROVENANCE_SHAPE_ERROR", wid)
            elif e["action"] not in ("removed", "rewritten"):
                bad(f"{wid}: edits action {e['action']!r} not in removed/rewritten",
                    "PROVENANCE_VALUE_INVALID", wid)

    fail = t["failure"]
    if fail is not None:
        if not isinstance(fail, dict) or set(fail) != FAILURE_KEYS:
            bad(f"{wid}: failure keys {sorted(fail) if isinstance(fail, dict) else '?'} "
                f"!= {sorted(FAILURE_KEYS)}", "OBSTRUCTION_SHAPE_ERROR", wid)
        else:
            if fail["code"] not in FAILURE_CODES:
                bad(f"{wid}: failure code {fail['code']!r} outside the fixed taxonomy",
                    "OBSTRUCTION_CODE_INVALID", wid)
            if not (isinstance(fail["quotes"], list) and fail["quotes"]):
                bad(f"{wid}: failure declaration without quotations — "
                    "obstruction claims require verbatim quotes",
                    "OBSTRUCTION_EVIDENCE_MISSING", wid)
            else:
                for q in fail["quotes"]:
                    if not isinstance(q, str) or norm(q) not in norm(task_md):
                        bad(f"{wid}: failure quote does not locate in the task file",
                            "QUOTE_NOT_LOCATABLE", wid)

    if not isinstance(t["notes"], str):
        bad(f"{wid}: notes is not a string", "NOTES_TYPE_ERROR", wid)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("submission", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()

    raw = a.submission.read_bytes()
    sub_sha = hashlib.sha256(raw).hexdigest()
    try:
        sub = json.loads(raw)
        if not isinstance(sub, dict):
            raise ValueError("top-level value is not an object")
    except Exception as e:
        bad(f"submission is not a parseable JSON object: {e}", "INVALID_SERIALIZATION")
        sub = None

    tasks: dict = {}
    if sub is not None:
        tmpl = json.loads((PKG / "output_template.json").read_text())

        if sub.get("schema_version") != SCHEMA_WRITER:
            bad(f"schema_version {sub.get('schema_version')!r} != {SCHEMA_WRITER!r}",
                "MISSING_REQUIRED_METADATA")
        if not (sub.get("writer_id") or "").strip():
            bad("writer_id is empty", "MISSING_REQUIRED_METADATA")
        tasks = sub.get("tasks")
        if not isinstance(tasks, dict):
            bad("tasks missing or not an object", "TASK_SET_ERROR")
            tasks = {}
        missing = sorted(set(tmpl["tasks"]) - set(tasks))
        unknown = sorted(set(tasks) - set(tmpl["tasks"]))
        if missing:
            bad(f"{len(missing)} eligible task(s) absent — no task may be dropped: "
                f"{missing[:6]}", "TASK_SET_ERROR")
        if unknown:
            bad(f"unknown task ids: {unknown[:6]}", "TASK_SET_ERROR")

        key = json.loads(
            (HERE / "writer_handoff/sealed/_KEY_DO_NOT_SHOW_WRITER.json").read_text())
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
    res = {"submission": str(a.submission), "problems": problems, "issues": issues,
           "accepted": not problems, "n_tasks": len(tasks),
           "submission_sha256": sub_sha,
           "failure_declarations": sum(1 for t in tasks.values()
                                       if isinstance(t, dict) and t.get("failure"))}
    if not problems:
        print(f"\nMECHANICAL INVARIANTS OK — {res['n_tasks']} candidates, "
              f"{res['failure_declarations']} failure declaration(s) recorded (not judged)")
        print(f"submission sha256: {res['submission_sha256']}")
    else:
        print(f"\nNOT ACCEPTED — {len(problems)} problem(s); resubmission per Amendment 3 "
              "(A1–A3 only; unrepairable flags end the pathway)")
    if a.json:
        a.json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
