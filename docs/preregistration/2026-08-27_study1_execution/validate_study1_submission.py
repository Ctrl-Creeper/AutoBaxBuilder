"""Schema, completeness, and provenance validation for one Study-1 run submission.

Frozen before either run starts. It validates one submission in isolation: it does not
open the sealed key, does not score anything, and cannot see the other run's output.

It checks exactly four things and judges nothing:
  - schema and completeness against the run's own answers_template.json;
  - provenance: the submission echoes the package's PACKET_FINGERPRINT;
  - a determined case carries a non-empty quote (invalid per Definition D otherwise);
  - the quote locates, after whitespace/case normalisation, inside the S_t actually
    presented in that task's packet file — closing the Round-2 instrument gap where a
    quote was required but never checked against S. Locating a quote is substring
    containment, never an assessment of whether the determination is right.

Usage:
    validate_study1_submission.py <answers.json> --package DIR [--json OUT]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

SCHEMA_VERSION = "study1-run-v1"
CONFIDENCE = {"clear", "tie_break"}
TASK_KEYS = {"J1", "notes"}
J1_KEYS = {"case", "determined", "quote", "confidence"}
BEGIN_S = "<<<BEGIN SPECIFICATION S>>>"
END_S = "<<<END SPECIFICATION S>>>"

problems: list[str] = []


def bad(msg: str) -> None:
    problems.append(msg)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def s_t_of(package: Path, tid: str) -> str | None:
    p = package / "tasks" / f"{tid}.md"
    if not p.exists():
        return None
    text = p.read_text()
    if BEGIN_S not in text or END_S not in text:
        return None
    return text.split(BEGIN_S, 1)[1].split(END_S, 1)[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("submission", type=Path)
    ap.add_argument("--package", type=Path, required=True,
                    help="the run's own isolated package; the other run's is never read")
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()

    tmpl = json.loads((a.package / "answers_template.json").read_text())
    fingerprint = (a.package / "PACKET_FINGERPRINT").read_text().strip()
    sub = json.loads(a.submission.read_text())

    if sub.get("schema_version") != SCHEMA_VERSION:
        bad(f"schema_version is {sub.get('schema_version')!r}, expected {SCHEMA_VERSION!r}")
    if not (sub.get("coder_id") or "").strip():
        bad("coder_id is empty")
    if sub.get("packet_fingerprint_sha256") != fingerprint:
        bad("packet_fingerprint_sha256 does not match the package's PACKET_FINGERPRINT")

    tasks = sub.get("tasks")
    if not isinstance(tasks, dict):
        bad("tasks is missing or not an object")
        tasks = {}

    missing = sorted(set(tmpl["tasks"]) - set(tasks))
    unknown = sorted(set(tasks) - set(tmpl["tasks"]))
    if missing:
        bad(f"{len(missing)} task(s) absent: {missing[:6]}")
    if unknown:
        bad(f"task ids with no counterpart in the template: {unknown[:6]}")

    conf, det = Counter(), 0
    for tid in sorted(set(tmpl["tasks"]) & set(tasks)):
        t, want = tasks[tid], tmpl["tasks"][tid]
        if not isinstance(t, dict) or set(t) != TASK_KEYS:
            bad(f"{tid}: keys are {sorted(t) if isinstance(t, dict) else '?'}, "
                f"expected exactly {sorted(TASK_KEYS)} — a missing key is an error, not a default")
            continue

        s_t = s_t_of(a.package, tid)
        if s_t is None:
            bad(f"{tid}: packet task file or its S markers not found — cannot locate quotes")

        j1 = t["J1"]
        if not isinstance(j1, list) or len(j1) != len(want["J1"]):
            bad(f"{tid}: J1 has {len(j1) if isinstance(j1, list) else '?'} entries, "
                f"expected {len(want['J1'])}")
            continue
        seen = set()
        for e in j1:
            if not isinstance(e, dict) or set(e) != J1_KEYS:
                bad(f"{tid}: a J1 entry has keys {sorted(e) if isinstance(e, dict) else '?'}, "
                    f"expected {sorted(J1_KEYS)}")
                continue
            seen.add(e["case"])
            if not isinstance(e["determined"], bool):
                bad(f"{tid} case {e['case']}: determined is not recorded as a boolean")
            elif e["determined"]:
                det += 1
                q = (e.get("quote") or "").strip()
                if not q:
                    bad(f"{tid} case {e['case']}: determined without a quote — "
                        "invalid per Definition D")
                elif s_t is not None and norm(q) not in norm(s_t):
                    bad(f"{tid} case {e['case']}: quote does not locate in the presented S")
            if e.get("confidence") not in CONFIDENCE:
                bad(f"{tid} case {e['case']}: confidence is {e.get('confidence')!r}, "
                    f"expected one of {sorted(CONFIDENCE)}")
            else:
                conf[e["confidence"]] += 1
        if seen != {c["case"] for c in want["J1"]}:
            bad(f"{tid}: case numbers do not match the template")

        if not isinstance(t["notes"], str):
            bad(f"{tid}: notes is not a string")

    for p in problems[:30]:
        print(f"  PROBLEM {p}")
    if len(problems) > 30:
        print(f"  … and {len(problems) - 30} more")

    res = {"submission": str(a.submission), "problems": problems, "accepted": not problems,
           "tasks": len(tasks), "cases_recorded": sum(len(t.get("J1", [])) for t in tasks.values()
                                                      if isinstance(t, dict)),
           "confidence_counts": dict(conf), "determined_count": det}
    if not problems:
        res["submission_sha256"] = hashlib.sha256(a.submission.read_bytes()).hexdigest()
        print(f"\nSCHEMA, COMPLETENESS AND PROVENANCE OK — {res['tasks']} tasks, "
              f"{res['cases_recorded']} cases")
        print(f"submission sha256: {res['submission_sha256']}")
        print("Freeze this hash. Do not reveal the key, score, or compare runs until BOTH "
              "submissions are independently frozen.")
    else:
        print(f"\nNOT ACCEPTED — {len(problems)} problem(s). Return to this run only. "
              "The other run's output is never a reference for repairing this one.")
    if a.json:
        a.json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
