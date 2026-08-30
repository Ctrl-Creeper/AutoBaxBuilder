"""Study 3 — Amendment 3 native resubmission gate (writer instrument only).

Implements the frozen Round-2 resubmission DISCIPLINE — the first submission is the
permanent substantive anchor; repairs are non-substantive, pre-enumerated, and licensed
only by machine-readable flags from the frozen candidate validator — implemented
prospectively against the frozen Study-3 writer schema, before any writer output exists
(AMENDMENT_3_study3_native_resubmission_gate.md; GAP-4 discovery record therein).

This file reads exactly three inputs: the FIRST_SUBMISSION_ANCHOR bytes, the frozen
candidate validator's machine report on those bytes (bound by submission_sha256), and
the resubmission. Nothing else is reachable from here — the coder-side §3 artifacts,
the measured-membership manifest, Study-1/Round-2 outcomes, future witness-check
results and final classifications are all outside its ban-audited surface.

Substantive anchor (never repairable): the six candidate fields — description, context,
arguments, return, raise, security_policy (null vs string vs absent all distinct) —
sufficiency_evidence, the obstruction declaration (failure null-vs-object; code,
at_case, detail, quotes values), notes, the value content / length / order of edits[],
and the task id set. Repairable, flag-licensed only:
  A1 serialization/container — BOM, markdown fences, stray bytes outside the outermost
     object, dict-key casing, a bare edits object promoted to a one-entry list;
  A2 required-metadata completion — schema_version to its fixed constant; writer_id
     filled only if empty;
  A3 edits[] container/key-shape with all five parsed values unchanged.
There is no A4 and none may ever be created (Amendment 3, clause 3): any validator flag
outside the licensing map ends the resubmission pathway — the first submission stands,
permanently, as the formal writer output (UNREPAIRABLE_FIRST_SUBMISSION; never deletes
a task, never auto-classifies anything).

Usage:
    resubmission_gate_study3.py --anchor <first_submission.json>
    resubmission_gate_study3.py --gate <resubmission.json> --report <validator_report.json>
                                [--anchor-file PATH] [--delta OUT]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from study3_pins import EDITABLE_FIELDS, SCHEMA_WRITER

HERE = Path(__file__).resolve().parent
ANCHOR_DEFAULT = HERE / "writer_handoff" / "submissions" / "FIRST_SUBMISSION_ANCHOR.json"

ABSENT = "\x00ABSENT\x00"          # missing key ≠ null ≠ "" in every comparison
SPEC_ALL = tuple(EDITABLE_FIELDS) + ("security_policy",)
EDIT_FIELDS = ("field", "original", "action", "replacement", "why")

# frozen licensing map (Amendment 3 clause 5); every other code is unrepairable
REPAIR_CLASS = {
    "INVALID_SERIALIZATION": "A1",
    "TASK_SHAPE_ERROR": "A1",
    "CANDIDATE_SCHEMA_ERROR": "A1",
    "OBSTRUCTION_SHAPE_ERROR": "A1",
    "MISSING_REQUIRED_METADATA": "A2",
    "PROVENANCE_SHAPE_ERROR": "A3",
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _fence(s: str) -> str:
    m = re.search(r"```(?:json)?\s*(.*?)```", s, re.DOTALL)
    return m.group(1) if m else s


def _span(s: str) -> str:
    return s[s.index("{"): s.rindex("}") + 1]


def recover(raw: bytes) -> tuple[dict | None, list[str]]:
    """Frozen A1 container recovery — deterministic transforms of the anchor bytes.

    No writer re-authoring can enter here: the parsed object is a pure function of the
    anchor. Returns (object, transforms-used) or (None, []) when nothing parses."""
    txt = raw.decode("utf-8", errors="replace")
    for name, t in (("as-is", lambda s: s),
                    ("bom-strip", lambda s: s.lstrip("\ufeff")),
                    ("fence-strip", _fence),
                    ("brace-span", _span)):
        try:
            obj = json.loads(t(txt))
        except Exception:
            continue
        if isinstance(obj, dict):
            return obj, ([] if name == "as-is" else [name])
    return None, []


def _lk(d: dict, log: list[str], tag: str) -> dict:
    out: dict = {}
    for k, v in d.items():
        nk = k.lower() if isinstance(k, str) else k
        if nk in out:            # casing collision: keep verbatim, substance will judge
            nk = k
        if nk != k:
            log.append(tag)
        out[nk] = v
    return out


def canon(sub: dict, log: list[str]) -> dict:
    """Frozen canonicalization: erases exactly the A1/A3 repair surface, nothing more.

    Key casing lowercased everywhere except task ids; a bare edits object with entry
    keys becomes a one-entry list. Values are never touched."""
    s = _lk(dict(sub), log, "A1")
    tasks = s.get("tasks")
    if isinstance(tasks, dict):
        nt = {}
        for tid, t in tasks.items():                 # task ids stay verbatim
            if isinstance(t, dict):
                t = _lk(dict(t), log, "A1")
                if isinstance(t.get("spec"), dict):
                    t["spec"] = _lk(dict(t["spec"]), log, "A1")
                e = t.get("edits")
                if isinstance(e, dict):
                    e = [e]
                    log.append("A3")
                if isinstance(e, list):
                    t["edits"] = [(_lk(dict(x), log, "A3") if isinstance(x, dict) else x)
                                  for x in e]
                if isinstance(t.get("failure"), dict):
                    t["failure"] = _lk(dict(t["failure"]), log, "A1")
            nt[tid] = t
        s["tasks"] = nt
    return s


def candidate_hash(t: dict) -> str:
    """Per-task hash over all six candidate fields (Amendment 3 clause 2)."""
    spec = t.get("spec") if isinstance(t.get("spec"), dict) else {}
    body = {f: spec.get(f, ABSENT) for f in SPEC_ALL}
    return sha(json.dumps(body, sort_keys=True, ensure_ascii=False).encode())


def substance_hash(t: dict) -> str:
    """Redundant whole-task substantive-object hash: candidate + obstruction declaration
    + evidence + notes + edit substance (field lowercased; values verbatim)."""
    spec = t.get("spec") if isinstance(t.get("spec"), dict) else {}
    raw_edits = t.get("edits")
    if isinstance(raw_edits, list):
        edits = []
        for e in raw_edits:
            if isinstance(e, dict):
                edits.append([str(e.get("field", ABSENT)).lower()]
                             + [e.get(k, ABSENT) for k in EDIT_FIELDS[1:]])
            else:
                edits.append(ABSENT)
    else:
        edits = ABSENT
    body = {"spec": {f: spec.get(f, ABSENT) for f in SPEC_ALL},
            "sufficiency_evidence": t.get("sufficiency_evidence", ABSENT),
            "failure": t.get("failure", ABSENT),
            "notes": t.get("notes", ABSENT),
            "edits": edits}
    return sha(json.dumps(body, sort_keys=True, ensure_ascii=False).encode())


def gate(anchor_raw: bytes, report: dict, resub_raw: bytes) -> dict:
    hard: list[str] = []
    res: dict = {"gate": "study3-amendment3-v1", "anchor_sha256": sha(anchor_raw),
                 "verdict": None, "per_task": {}, "hard_failures": hard,
                 "accepted": False}

    # the report must be the frozen validator's report ON THE ANCHOR — verified, not asserted
    if report.get("submission_sha256") != res["anchor_sha256"]:
        hard.append("validator report does not bind to the anchor bytes "
                    "(submission_sha256 mismatch); refusing to gate")
        res["verdict"] = "REJECTED_RESUBMISSION"
        return res

    issue_list = report.get("issues")
    if not isinstance(issue_list, list):
        hard.append("validator report carries no machine-readable issues[]")
        res["verdict"] = "REJECTED_RESUBMISSION"
        return res
    codes = sorted({i.get("code") for i in issue_list})
    task_flags: dict[str, set] = {}
    for i in issue_list:
        if i.get("task"):
            task_flags.setdefault(i["task"], set()).add(i.get("code"))
    res["codes"] = codes
    res["licensed"] = sorted({REPAIR_CLASS[c] for c in codes if c in REPAIR_CLASS})

    if not codes:
        res["verdict"] = "ACCEPT_FIRST"
        hard.append("no validator flag exists — nothing may be resubmitted; "
                    "the first submission is the formal writer output")
        return res

    unrep = sorted(c for c in codes if c not in REPAIR_CLASS)
    if unrep:
        res["verdict"] = "UNREPAIRABLE_FIRST_SUBMISSION"
        res["unrepairable_codes"] = unrep
        res["per_task"] = {w: {"outcome": ("UNREPAIRABLE_FIRST_SUBMISSION"
                                           if (fl - set(REPAIR_CLASS)) else "flag_repairable")}
                           for w, fl in sorted(task_flags.items())}
        hard.append(f"flag(s) {unrep} admit no frozen repair class; no A4 may be created "
                    "(Amendment 3 clause 3) — the first submission stands, permanently, "
                    "as the formal writer output; no task is deleted and nothing is "
                    "auto-classified (downstream per protocol + GAP-5 ruling)")
        return res

    # ---- all flags repairable: substantive-identity gating -------------------------
    aobj, transforms = recover(anchor_raw)
    res["anchor_transforms"] = transforms
    if aobj is None:
        res["verdict"] = "UNREPAIRABLE_FIRST_SUBMISSION"
        hard.append("no substantive content is recoverable from the anchor by the frozen "
                    "A1 transforms — there is nothing a non-substantive repair could "
                    "restore; the first submission stands as the formal writer output")
        return res
    alog: list[str] = []
    A = canon(aobj, alog)

    try:
        robj = json.loads(resub_raw)
        if not isinstance(robj, dict):
            raise ValueError("top-level value is not an object")
    except Exception as e:
        hard.append(f"resubmission is not a parseable JSON object: {e}")
        res["verdict"] = "REJECTED_RESUBMISSION"
        return res
    rlog: list[str] = []
    canon(robj, rlog)
    if rlog:
        hard.append("resubmission itself carries serialization anomalies (casing/"
                    "container); a repaired artifact must be exactly canonical")

    if robj.get("schema_version") != SCHEMA_WRITER:
        hard.append(f"schema_version {robj.get('schema_version')!r} != {SCHEMA_WRITER!r}")
    a_wid = A.get("writer_id") if isinstance(A.get("writer_id"), str) else ""
    r_wid = robj.get("writer_id") if isinstance(robj.get("writer_id"), str) else ""
    if a_wid.strip() and r_wid != a_wid:
        hard.append(f"writer_id mutated: {a_wid!r} -> {r_wid!r} (completion-only field)")

    at = A.get("tasks") if isinstance(A.get("tasks"), dict) else {}
    rt = robj.get("tasks") if isinstance(robj.get("tasks"), dict) else {}
    if set(at) != set(rt):
        hard.append("task id set changed — a resubmission never alters the manifest "
                    f"(missing {sorted(set(at) - set(rt))[:4]}, "
                    f"added {sorted(set(rt) - set(at))[:4]})")

    for tid in sorted(set(at) & set(rt)):
        ta, tr = at[tid], rt[tid]
        row = {"substantive_hash_anchor": substance_hash(ta),
               "substantive_hash_resub": substance_hash(tr),
               "candidate_hash_anchor": candidate_hash(ta),
               "candidate_hash_resub": candidate_hash(tr)}
        if row["candidate_hash_resub"] != row["candidate_hash_anchor"]:
            hard.append(f"{tid}: candidate S' changed — all six fields are substantively "
                        "frozen under every repair class")
        if row["substantive_hash_resub"] != row["substantive_hash_anchor"]:
            hard.append(f"{tid}: substantive object changed (obstruction declaration, "
                        "evidence, notes or edit substance) — nothing substantive is "
                        "repairable")
        pa = (ta.get("spec") or {}).get("security_policy", ABSENT)
        pr = (tr.get("spec") or {}).get("security_policy", ABSENT)
        if (pa is None) != (pr is None) or pa != pr:
            hard.append(f"{tid}: security_policy changed (null/string/absent are "
                        "distinct values; conversion is substantive)")
        row["outcome"] = "ACCEPT_REPAIRED" if tid in task_flags else "ACCEPT_FIRST"
        res["per_task"][tid] = row

    used = set()
    if transforms or "A1" in alog:
        used.add("A1")
    if "A3" in alog:
        used.add("A3")
    if A.get("schema_version") != robj.get("schema_version") or a_wid != r_wid:
        used.add("A2")
    res["used"] = sorted(used)
    unlicensed = used - set(res["licensed"])
    if unlicensed:
        hard.append(f"repair class(es) {sorted(unlicensed)} used without a licensing "
                    "validator flag — repairs answer flags, never anticipate them")

    res["verdict"] = "REJECTED_RESUBMISSION" if hard else "ACCEPT_REPAIRED"
    res["accepted"] = not hard
    if res["accepted"]:
        res["next"] = ("frozen validate_study3_candidate.py must now pass on this "
                       "resubmission; both gates in that order before any freeze")
    else:
        for row in res["per_task"].values():
            row["outcome"] = "REJECTED"
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchor", type=Path, help="record the first submission as the "
                    "permanent substantive anchor (refuses overwrite)")
    ap.add_argument("--gate", type=Path, help="resubmission to gate")
    ap.add_argument("--report", type=Path, help="frozen validator machine report on the anchor")
    ap.add_argument("--anchor-file", type=Path, default=ANCHOR_DEFAULT)
    ap.add_argument("--delta", type=Path)
    a = ap.parse_args()

    if a.anchor:
        if a.anchor_file.exists():
            sys.exit("FIRST_SUBMISSION_ANCHOR already exists; the anchor is permanent "
                     "and is never replaced (Amendment 3 clause 1)")
        raw = a.anchor.read_bytes()
        a.anchor_file.parent.mkdir(parents=True, exist_ok=True)
        a.anchor_file.write_bytes(raw)
        a.anchor_file.with_suffix(".sha256").write_text(
            f"{sha(raw)}  {a.anchor_file.name}\n")
        print(f"FIRST_SUBMISSION_ANCHOR recorded, sha256 {sha(raw)}")
        return

    if not (a.gate and a.report):
        sys.exit("usage: --anchor FILE | --gate RESUB --report REPORT")
    if not a.anchor_file.exists():
        sys.exit("no FIRST_SUBMISSION_ANCHOR exists; record the first submission before "
                 "any resubmission is even readable")
    res = gate(a.anchor_file.read_bytes(), json.loads(a.report.read_text()),
               a.gate.read_bytes())
    print(f"  flags {res.get('codes')}  licensed {res.get('licensed', [])}  "
          f"used {res.get('used', [])}")
    for h in res["hard_failures"][:25]:
        print(f"  HARD  {h}")
    if len(res["hard_failures"]) > 25:
        print(f"  … and {len(res['hard_failures']) - 25} more")
    if a.delta:
        a.delta.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"\nVERDICT: {res['verdict']}")
    sys.exit(0 if res["accepted"] else 1)


if __name__ == "__main__":
    main()
