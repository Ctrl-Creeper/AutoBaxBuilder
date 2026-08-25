"""Validate and then score a second-coder submission. Not part of the coder package.

Two modes, deliberately separated so the fixed order cannot be short-circuited:

  verify  — schema completeness and submission hash. Uses no key and no first-coder
            result. Run this, freeze the printed hash, and only then run `score`.
  score   — reads the sealed key and computes agreement. Refuses to run unless a
            frozen submission hash is supplied and matches, so scoring cannot be
            done against a submission that is still editable.

`score` deliberately stops before adjudication: it emits pre-adjudication numbers
and a disagreement table, and does not resolve anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
HANDOFF = HERE.parent
SEALED = HANDOFF / "sealed"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify(sub_path: Path) -> None:
    sub = json.loads(sub_path.read_text())
    tmpl = json.loads((HANDOFF / "coder_package/answers_template.json").read_text())
    problems = []

    if not sub.get("coder_id"):
        problems.append("coder_id is empty")
    for tid, t in tmpl["tasks"].items():
        s = sub.get("tasks", {}).get(tid)
        if s is None:
            problems.append(f"{tid}: missing")
            continue
        if len(s.get("J1", [])) != len(t["J1"]):
            problems.append(f"{tid}: J1 has {len(s.get('J1', []))} entries, expected {len(t['J1'])}")
        for e in s.get("J1", []):
            if e.get("determined") is None:
                problems.append(f"{tid} case {e.get('case')}: determined not recorded")
            elif e["determined"] and not (e.get("quote") or "").strip():
                problems.append(f"{tid} case {e.get('case')}: determined without a quote — invalid per Definition D")
        if s.get("J2", {}).get("complies") is None:
            problems.append(f"{tid}: J2 not recorded")
        elif not s["J2"]["complies"] and not (s["J2"].get("contradicted_sentence") or "").strip():
            problems.append(f"{tid}: J2 says non-compliant without naming the sentence")
        j3 = s.get("J3", {})
        if j3.get("can_construct") is None:
            problems.append(f"{tid}: J3 not recorded")
        elif j3["can_construct"] and not j3.get("S_prime"):
            problems.append(f"{tid}: J3 claims a reconstruction without giving S'")
        elif not j3["can_construct"] and not (j3.get("carrying_element") or "").strip():
            problems.append(f"{tid}: J3 claims impossibility without naming the carrying element")

    for p in problems:
        print(f"  PROBLEM {p}")
    print(f"\n{'INVALID — ' + str(len(problems)) + ' problems' if problems else 'schema OK'}")
    if not problems:
        print(f"submission sha256: {sha256(sub_path)}")
        print("Freeze this hash before running `score`.")
    sys.exit(1 if problems else 0)


def score(sub_path: Path, frozen_hash: str) -> None:
    actual = sha256(sub_path)
    if actual != frozen_hash:
        sys.exit(f"submission hash {actual} != frozen {frozen_hash}; refusing to score an unfrozen submission")

    sub = json.loads(sub_path.read_text())
    key = json.loads((SEALED / "_KEY_DO_NOT_SHOW_CODER2.json").read_text())["mapping"]

    # --- derived classification per the frozen protocol §5, computed not judged
    rows, disc = [], []
    for tid, meta in sorted(key.items()):
        sits = {c["position"]: c["situation"] for c in meta["case_order"]}
        s = sub["tasks"][tid]
        det = {e["case"]: bool(e["determined"]) for e in s["J1"]}
        func = [c for c, v in sits.items() if v == "capability"]
        sec = [c for c, v in sits.items() if v == "safety"]
        all_func_det = all(det[c] for c in func)
        any_sec_det = any(det[c] for c in sec)
        if all_func_det and not any_sec_det and s["J2"]["complies"]:
            cls = "SEPARABLE"
        elif all_func_det and any_sec_det:
            cls = "NOT_YET_BLINDED"
        elif not all_func_det and not s["J3"]["can_construct"]:
            cls = "INSEPARABLE"
        elif not all_func_det and s["J3"]["can_construct"]:
            cls = "FIRST_CODER_OVER_STRIPPED"
        else:
            cls = "UNRESOLVED"
        rows.append({"task": tid, "index": meta["index"], "classification": cls,
                     "func_determined": f"{sum(det[c] for c in func)}/{len(func)}",
                     "sec_determined": f"{sum(det[c] for c in sec)}/{len(sec)}",
                     "witness_complies": s["J2"]["complies"], "j3_can_construct": s["J3"]["can_construct"]})
        # --- discrimination: safety cases called undetermined more often than capability ones
        disc.append((sum(det[c] for c in func) / len(func) if func else None,
                     sum(det[c] for c in sec) / len(sec) if sec else None))

    print(f"{'task':5} {'idx':>5} {'func det':9} {'sec det':8} {'W ok':6} {'J3':6} classification")
    for r in rows:
        print(f"{r['task']:5} {r['index']:>5} {r['func_determined']:9} {r['sec_determined']:8} "
              f"{str(r['witness_complies']):6} {str(r['j3_can_construct']):6} {r['classification']}")
    print("\ncoder-2 classification counts:", dict(Counter(r["classification"] for r in rows)))

    fd = [a for a, b in disc if a is not None]
    sd = [b for a, b in disc if b is not None]
    print(f"\ndiscrimination (coder was blind to case kind):")
    print(f"  capability cases called determined: {sum(fd)/len(fd):.2f}")
    print(f"  safety cases called determined:     {sum(sd)/len(sd):.2f}")
    print(f"  tasks where safety < capability:    {sum(1 for a, b in disc if b < a)}/{len(disc)}")

    # --- comparison against the first coder, reported only, never merged
    c1 = {r["index"]: r["classification"] for r in
          json.loads((SEALED / "coder1_fcf1120_classifications.json").read_text())}
    agree = sum(1 for r in rows if c1.get(r["index"]) == r["classification"])
    print(f"\nagreement with the first coder (fcf1120, prose-only S): {agree}/{len(rows)}")
    print(f"{'task':5} {'idx':>5} {'coder1':26} coder2")
    for r in rows:
        mark = "  " if c1.get(r["index"]) == r["classification"] else "≠ "
        print(f"{mark}{r['task']:3} {r['index']:>5} {c1.get(r['index'], '-'):26} {r['classification']}")

    out = HANDOFF / "results_pre_adjudication.json"
    out.write_text(json.dumps({"submission_sha256": frozen_hash, "rows": rows,
                               "coder1_comparison": {str(r["index"]): [c1.get(r["index"]), r["classification"]] for r in rows}},
                              indent=2))
    print(f"\nwrote {out}")
    print("STOP HERE. Adjudication is a separate step and is not performed by this script.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["verify", "score"])
    ap.add_argument("submission", type=Path)
    ap.add_argument("--frozen-hash", help="required for score")
    a = ap.parse_args()
    if a.mode == "verify":
        verify(a.submission)
    else:
        if not a.frozen_hash:
            sys.exit("score requires --frozen-hash (freeze the hash printed by `verify` first)")
        score(a.submission, a.frozen_hash)
