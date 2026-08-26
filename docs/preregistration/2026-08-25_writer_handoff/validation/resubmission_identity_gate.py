"""Identity gate for a provenance-completion resubmission.

The first submission was not accepted for two mechanical reasons: `edits[].field`
used display-cased names, and clause-level changes were left undeclared. The
remedy is to complete the record of edits already made — **not** to author
anything again.

So the candidate specifications are frozen at the baseline. This gate exists to
make that enforceable rather than merely requested: the writer is now aware of
what the validator's H9 looks for, and without a byte-identity constraint they
could quietly reword a candidate to need fewer declarations. That would let
validator feedback reach the specifications, which are the material the blinded
coding runs are supposed to judge untouched.

Allowed to change, and nothing else:

  A1  `edits[].field` normalised to the schema's lowercase key
  A2  new entries appended to `edits[]`
  A3  a structural repair to a `failure` object that violates the schema

Everything else — every character of every candidate field, every existing edit
body, `sufficiency_evidence`, `notes`, `failure` content, the task set,
`writer_id`, `schema_version` — must be identical. Any difference outside the
allowlist is a hard failure.

This gate does not replace the frozen writer validator. A resubmission is accepted
only when **both** pass.

Usage:
    resubmission_identity_gate.py <resubmission.json> [--baseline PATH] [--delta OUT]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HANDOFF = Path(__file__).resolve().parent.parent
BASELINE = HANDOFF / "submissions/writer_output_v1_baseline.json"
EDITABLE = ("description", "context", "arguments", "return", "raise")
FAILURE_CODES = {"F1_LIST_COUPLING", "F2_SIGNATURE_CARRIER", "F3_PREAMBLE_CARRIER",
                 "F4_RETURN_CONTRACT_CARRIER", "F5_MATERIAL_DEFECT"}

hard: list[str] = []


def fail(msg: str) -> None:
    hard.append(msg)


def spec_hash(spec: dict) -> str:
    """Order-independent digest over the five candidate fields, byte-exact."""
    return hashlib.sha256(
        json.dumps({f: spec.get(f) for f in EDITABLE}, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def edit_body(e: dict) -> tuple:
    """An edit's content with the field name lowercased, so A1 is invisible here."""
    return (str(e.get("field", "")).strip().lower(), e.get("original"),
            e.get("action"), e.get("replacement"), e.get("why"))


def gate(base: dict, new: dict) -> dict:
    if new.get("schema_version") != base.get("schema_version"):
        fail(f"schema_version changed: {base.get('schema_version')!r} -> {new.get('schema_version')!r}")
    if new.get("writer_id") != base.get("writer_id"):
        fail(f"writer_id changed: {base.get('writer_id')!r} -> {new.get('writer_id')!r}")

    bt, nt = base.get("tasks", {}), new.get("tasks", {})
    if set(bt) != set(nt):
        fail(f"task id set changed — added {sorted(set(nt) - set(bt))[:5]}, "
             f"removed {sorted(set(bt) - set(nt))[:5]}; a resubmission never alters the manifest")
    if len(nt) != len(bt):
        fail(f"task count changed: {len(bt)} -> {len(nt)}")

    rows = []
    for wid in sorted(set(bt) & set(nt)):
        b, n = bt[wid], nt[wid]
        row = {"task": wid, "casing_fixed": 0, "provenance_added": 0,
               "spec_hash_before": None, "spec_hash_after": None, "non_allowlisted": []}

        if not isinstance(n, dict):
            row["non_allowlisted"].append("task record is not an object")
            rows.append(row)
            fail(f"{wid}: task record is not an object")
            continue

        # --- A-invariant: candidate prose is frozen
        hb, hn = spec_hash(b.get("spec", {})), spec_hash(n.get("spec", {}))
        row["spec_hash_before"], row["spec_hash_after"] = hb, hn
        if hb != hn:
            changed = [f for f in EDITABLE if b.get("spec", {}).get(f) != n.get("spec", {}).get(f)]
            row["non_allowlisted"].append(f"candidate spec text changed in {changed}")
            fail(f"{wid}: candidate specification changed in {changed} — the prose is frozen; "
                 "this resubmission completes provenance, it does not re-author")
        if set(n.get("spec", {})) != set(b.get("spec", {})):
            row["non_allowlisted"].append("spec key set changed")
            fail(f"{wid}: spec key set changed")

        # --- failure: identical, unless the baseline object was itself schema-invalid
        fb, fn = b.get("failure"), n.get("failure")
        if fb != fn:
            baseline_valid = fb is None or (
                isinstance(fb, dict) and set(fb) == {"code", "at_case", "detail"}
                and fb.get("code") in FAILURE_CODES)
            code_kept = (fb or {}).get("code") == (fn or {}).get("code") if isinstance(fb, dict) else fn is None
            if baseline_valid:
                row["non_allowlisted"].append("failure changed while the baseline was schema-valid")
                fail(f"{wid}: failure record changed although the baseline one was valid — "
                     "a validator result is never grounds for reinterpreting a task")
            elif not code_kept:
                row["non_allowlisted"].append("failure code changed during structural repair")
                fail(f"{wid}: structural repair to failure may not change the code")

        # --- edits: existing bodies frozen, appends allowed, casing normalisation allowed
        be, ne = b.get("edits", []), n.get("edits", [])
        if not isinstance(ne, list):
            row["non_allowlisted"].append("edits is not a list")
            fail(f"{wid}: edits is not a list")
        else:
            bodies_b = [edit_body(e) for e in be if isinstance(e, dict)]
            bodies_n = [edit_body(e) for e in ne if isinstance(e, dict)]
            if bodies_n[:len(bodies_b)] != bodies_b:
                row["non_allowlisted"].append("an existing edit entry was modified, removed or reordered")
                fail(f"{wid}: existing edit entries must survive unchanged and in order; "
                     "new declarations are appended")
            row["provenance_added"] = max(0, len(bodies_n) - len(bodies_b))
            row["casing_fixed"] = sum(
                1 for eb, en in zip(be, ne)
                if isinstance(eb, dict) and isinstance(en, dict)
                and eb.get("field") != en.get("field")
                and str(eb.get("field", "")).lower() == str(en.get("field", "")).lower())

        # --- everything else is frozen
        for k in ("sufficiency_evidence", "notes"):
            if b.get(k) != n.get(k):
                row["non_allowlisted"].append(f"{k} changed")
                fail(f"{wid}: {k} changed; only edits[] and its field casing may move")
        extra = set(n) - set(b)
        if extra:
            row["non_allowlisted"].append(f"unexpected keys {sorted(extra)}")
            fail(f"{wid}: unexpected keys {sorted(extra)}")

        rows.append(row)

    return {"baseline_sha256": None, "rows": rows,
            "totals": {"casing_fixed": sum(r["casing_fixed"] for r in rows),
                       "provenance_added": sum(r["provenance_added"] for r in rows),
                       "tasks_with_non_allowlisted": sum(1 for r in rows if r["non_allowlisted"])},
            "hard_failures": hard, "accepted": not hard}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("resubmission", type=Path)
    ap.add_argument("--baseline", type=Path, default=BASELINE)
    ap.add_argument("--delta", type=Path)
    a = ap.parse_args()

    base = json.loads(a.baseline.read_text())
    new = json.loads(a.resubmission.read_text())
    res = gate(base, new)
    res["baseline_sha256"] = hashlib.sha256(a.baseline.read_bytes()).hexdigest()

    t = res["totals"]
    print(f"  field-name casings corrected   {t['casing_fixed']}")
    print(f"  provenance entries added       {t['provenance_added']}")
    print(f"  tasks with non-allowlisted change  {t['tasks_with_non_allowlisted']}")
    print()
    for h in res["hard_failures"][:25]:
        print(f"  HARD  {h}")
    if len(res["hard_failures"]) > 25:
        print(f"  … and {len(res['hard_failures']) - 25} more")

    if a.delta:
        a.delta.write_text(json.dumps(res, indent=2, ensure_ascii=False))
        print(f"\nwrote {a.delta}")

    if res["accepted"]:
        print("\nIDENTITY GATE PASSED — every change lands in the allowlist.")
        print("Now run the frozen writer validator. Both must pass before the hash is frozen.")
    else:
        print(f"\nIDENTITY GATE FAILED — {len(res['hard_failures'])} non-allowlisted change(s).")
    sys.exit(0 if res["accepted"] else 1)


if __name__ == "__main__":
    main()
