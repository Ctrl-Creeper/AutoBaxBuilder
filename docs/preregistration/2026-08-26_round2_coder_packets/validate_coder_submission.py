"""Schema and completeness validation for one Round-2 coder submission.

Frozen before either run starts.

**It validates one submission in isolation.** It does not open the sealed key, does
not score anything, does not classify any task, and cannot see the other run's
output. Those steps are gated behind both submissions being independently frozen,
and a validator that peeked would make "independent" untrue at the first opportunity.

Case counts come from the frozen answer template, which every coder already holds,
so no withheld material is consulted to check completeness.

Usage:
    validate_coder_submission.py <coder_answers.json> --package DIR [--json OUT]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

SCHEMA_VERSION = "round2-coder-v1"
CONFIDENCE = {"clear", "tie_break"}
TASK_KEYS = {"J1", "J2", "J3", "notes"}
J1_KEYS = {"case", "determined", "quote", "confidence"}
J2_KEYS = {"contradicts_S", "contradicted_sentence"}
J3_KEYS = {"exists", "S_prime", "carrying_element", "reason"}

problems: list[str] = []


def bad(msg: str) -> None:
    problems.append(msg)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("submission", type=Path)
    ap.add_argument("--package", type=Path, required=True,
                    help="the coder's own isolated directory; the other run's is never read")
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()

    tmpl = json.loads((a.package / "answers_template.json").read_text())
    sub = json.loads(a.submission.read_text())

    if sub.get("schema_version") != SCHEMA_VERSION:
        bad(f"schema_version is {sub.get('schema_version')!r}, expected {SCHEMA_VERSION!r}")
    if not (sub.get("coder_id") or "").strip():
        bad("coder_id is empty")

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

        j1 = t["J1"]
        if not isinstance(j1, list) or len(j1) != len(want["J1"]):
            bad(f"{tid}: J1 has {len(j1) if isinstance(j1, list) else '?'} entries, "
                f"expected {len(want['J1'])}")
        else:
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
                    if not (e.get("quote") or "").strip():
                        bad(f"{tid} case {e['case']}: determined without a quote — invalid per Definition D")
                if e.get("confidence") not in CONFIDENCE:
                    bad(f"{tid} case {e['case']}: confidence is {e.get('confidence')!r}, "
                        f"expected one of {sorted(CONFIDENCE)}")
                else:
                    conf[e["confidence"]] += 1
            if seen != {c["case"] for c in want["J1"]}:
                bad(f"{tid}: case numbers do not match the template")

        j2 = t["J2"]
        if not isinstance(j2, dict) or set(j2) != J2_KEYS:
            bad(f"{tid}: J2 keys are {sorted(j2) if isinstance(j2, dict) else '?'}")
        elif not isinstance(j2["contradicts_S"], bool):
            bad(f"{tid}: J2.contradicts_S is not recorded as a boolean")
        elif j2["contradicts_S"] and not (j2.get("contradicted_sentence") or "").strip():
            bad(f"{tid}: J2 says W contradicts S without naming the sentence")

        j3 = t["J3"]
        if not isinstance(j3, dict) or set(j3) != J3_KEYS:
            bad(f"{tid}: J3 keys are {sorted(j3) if isinstance(j3, dict) else '?'}")
        elif not isinstance(j3["exists"], bool):
            bad(f"{tid}: J3.exists is not recorded as a boolean")
        elif not j3["exists"] and not (j3.get("carrying_element") or "").strip():
            bad(f"{tid}: J3 says no such specification exists without naming the carrying element")
        elif not (j3.get("reason") or "").strip():
            bad(f"{tid}: J3 has no reason recorded")

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
        print(f"\nSCHEMA AND COMPLETENESS OK — {res['tasks']} tasks, {res['cases_recorded']} cases")
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
