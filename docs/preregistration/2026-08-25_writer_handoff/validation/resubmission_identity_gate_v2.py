"""Resubmission identity gate v2 — provenance correction only.

**Amendment, not a replacement.** v1 (`4b55454c…`) stays in the record untouched and
governed the first resubmission. v2 exists because the frozen writer validator, run
on that resubmission, exposed two provenance-format defects v1's allowlist could not
be used to fix: an entry may only be appended or have its field lowercased, and both
defects require correcting an entry in place.

**This gate is not outcome-blind, and does not claim to be.** It was written after 54
validator failures had been seen. What it may therefore not do — and does not do — is
touch research content. It widens a metadata-correction allowlist and nothing else;
the candidate specifications remain byte-frozen, which is checked first and is the
invariant everything else is subordinate to.

Carried over from v1:
  A1  `edits[].field` normalised to the schema's lowercase key
  A2  new entries appended to `edits[]`
  A3  structural repair to a `failure` object violating the schema, code preserved

Added in v2, and only for entries the frozen validator itself flagged:
  A4.1  `action` "rewritten" -> "removed", only where the validator recorded a
        rewritten-with-empty-replacement contradiction. Never the reverse.
  A4.2  `original` expanded from an abbreviated quotation to the complete verbatim
        text, only where the validator recorded an untraceable quotation, and only
        if the new value exact-matches inside the frozen writer input.
  A4.3  `replacement` corrected for structural consistency with the entry's action,
        and only where non-empty values exact-match inside the frozen candidate.

The flagged set is read from the frozen validator report and independently
recomputed; the gate refuses to run if the two disagree, so "the validator
determined it" is verified rather than asserted.

Still forbidden: any character of any candidate field; semantic rewriting of
`failure`, `notes` or `sufficiency_evidence`; adding or removing a task; task
replacement; redesigning a specification from validator feedback; and touching the
writer validator.

Usage:
    resubmission_identity_gate_v2.py <resubmission.json> [--delta OUT]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HANDOFF = Path(__file__).resolve().parent.parent
SUB = HANDOFF / "submissions"
ANCHOR = SUB / "writer_output_v1_baseline.json"          # immutable spec anchor
PREV = SUB / "writer_output_v2_resubmission1.json"        # what this one is compared against
REPORT = SUB / "writer_validator_report_on_resubmission1.json"
TASKS = HANDOFF / "writer_package/tasks"

EDITABLE = ("description", "context", "arguments", "return", "raise")
FAILURE_CODES = {"F1_LIST_COUPLING", "F2_SIGNATURE_CARRIER", "F3_PREAMBLE_CARRIER",
                 "F4_RETURN_CONTRACT_CARRIER", "F5_MATERIAL_DEFECT"}

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_writer_output import norm, parse_original  # noqa: E402

hard: list[str] = []


def fail(msg: str) -> None:
    hard.append(msg)


def spec_hash(spec: dict) -> str:
    return hashlib.sha256(
        json.dumps({f: spec.get(f) for f in EDITABLE}, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def flagged_sets(prev: dict) -> tuple[set, set]:
    """Read the flagged entries from the frozen report, then verify by recomputation."""
    msgs = json.loads(REPORT.read_text())["hard_failures"]

    def parse(pattern):
        out = set()
        for m in msgs:
            if pattern in m:
                g = re.match(r"(W\d\d) edit (\d+)", m)
                if g:
                    out.add((g.group(1), int(g.group(2))))
        return out

    rep_action = parse("action is rewritten but no replacement is given")
    rep_quote = parse("the quoted original is not present in the frozen")

    rec_action, rec_quote = set(), set()
    for wid, t in prev["tasks"].items():
        orig = parse_original((TASKS / f"{wid}.md").read_text())
        for i, e in enumerate(t.get("edits", []), 1):
            if e.get("action") == "rewritten" and not (e.get("replacement") or "").strip():
                rec_action.add((wid, i))
            if norm(e.get("original", "")) and norm(e["original"]) not in norm(orig.get(e.get("field", ""), "")):
                rec_quote.add((wid, i))

    if rep_action != rec_action or rep_quote != rec_quote:
        sys.exit("the frozen validator report and the recomputed flagged set disagree; "
                 "refusing to run — the amendment's scope must be verifiable, not asserted")
    return rec_action, rec_quote


def gate(anchor: dict, prev: dict, new: dict) -> dict:
    fa, fq = flagged_sets(prev)

    for k in ("schema_version", "writer_id"):
        if new.get(k) != prev.get(k):
            fail(f"{k} changed: {prev.get(k)!r} -> {new.get(k)!r}")

    if set(new.get("tasks", {})) != set(prev.get("tasks", {})):
        fail("task id set changed; a resubmission never alters the manifest")

    rows = []
    for wid in sorted(set(prev.get("tasks", {})) & set(new.get("tasks", {}))):
        p, n = prev["tasks"][wid], new["tasks"][wid]
        a = anchor["tasks"].get(wid, {})
        row = {"task": wid, "action_corrected": 0, "quotation_expanded": 0,
               "replacement_corrected": 0, "provenance_added": 0,
               "spec_hash_before": None, "spec_hash_after": None, "non_allowlisted": []}

        # --- highest-priority invariant: candidate prose is frozen, against both
        #     the immediate predecessor and the original anchor
        hp, hn, ha = spec_hash(p.get("spec", {})), spec_hash(n.get("spec", {})), spec_hash(a.get("spec", {}))
        row["spec_hash_before"], row["spec_hash_after"] = hp, hn
        if hn != hp or hn != ha:
            changed = [f for f in EDITABLE if p.get("spec", {}).get(f) != n.get("spec", {}).get(f)]
            row["non_allowlisted"].append(f"candidate spec text changed in {changed}")
            fail(f"{wid}: candidate specification changed in {changed} — the prose is frozen "
                 "under every amendment; v2 widens metadata correction only")
        if set(n.get("spec", {})) != set(p.get("spec", {})):
            row["non_allowlisted"].append("spec key set changed")
            fail(f"{wid}: spec key set changed")

        for k in ("failure", "sufficiency_evidence", "notes"):
            if n.get(k) != p.get(k):
                valid = k != "failure" or (
                    p.get("failure") is None or
                    (isinstance(p["failure"], dict) and set(p["failure"]) == {"code", "at_case", "detail"}
                     and p["failure"].get("code") in FAILURE_CODES))
                row["non_allowlisted"].append(f"{k} changed")
                fail(f"{wid}: {k} changed"
                     + (" although the baseline record was schema-valid" if k == "failure" and valid else ""))
        if set(n) - set(p):
            row["non_allowlisted"].append(f"unexpected keys {sorted(set(n) - set(p))}")
            fail(f"{wid}: unexpected keys {sorted(set(n) - set(p))}")

        pe, ne = p.get("edits", []), n.get("edits", [])
        if not isinstance(ne, list) or len(ne) < len(pe):
            row["non_allowlisted"].append("edits shrank or is not a list")
            fail(f"{wid}: edits shrank or is not a list; entries are corrected in place or appended")
            rows.append(row)
            continue
        row["provenance_added"] = len(ne) - len(pe)

        frozen_input = parse_original((TASKS / f"{wid}.md").read_text())
        for i, (ep, en) in enumerate(zip(pe, ne), 1):
            if not isinstance(en, dict) or set(en) != set(ep):
                row["non_allowlisted"].append(f"edit {i} key set changed")
                fail(f"{wid} edit {i}: key set changed")
                continue
            if str(en.get("field", "")).lower() != str(ep.get("field", "")).lower():
                row["non_allowlisted"].append(f"edit {i} field retargeted")
                fail(f"{wid} edit {i}: field retargeted from {ep['field']!r} to {en['field']!r}")
            if en.get("why") != ep.get("why"):
                row["non_allowlisted"].append(f"edit {i} why changed")
                fail(f"{wid} edit {i}: why changed; A4 corrects structure, not rationale")

            # A4.1 — action
            if en.get("action") != ep.get("action"):
                if (wid, i) not in fa:
                    row["non_allowlisted"].append(f"edit {i} action changed without a validator flag")
                    fail(f"{wid} edit {i}: action changed but the validator flagged no contradiction here")
                elif not (ep.get("action") == "rewritten" and en.get("action") == "removed"):
                    row["non_allowlisted"].append(f"edit {i} action change outside A4.1")
                    fail(f"{wid} edit {i}: only rewritten -> removed is permitted, "
                         f"got {ep.get('action')!r} -> {en.get('action')!r}")
                else:
                    row["action_corrected"] += 1

            # A4.2 — original
            if en.get("original") != ep.get("original"):
                if (wid, i) not in fq:
                    row["non_allowlisted"].append(f"edit {i} original changed without a validator flag")
                    fail(f"{wid} edit {i}: quotation changed but the validator flagged no "
                         "traceability problem here")
                elif norm(en["original"]) not in norm(frozen_input.get(en.get("field", ""), "")):
                    row["non_allowlisted"].append(f"edit {i} expanded quotation does not match the input")
                    fail(f"{wid} edit {i}: the expanded quotation does not exact-match the frozen "
                         f"{en.get('field')} field — A4.2 permits completion, never substitution")
                elif norm(ep["original"].replace("...", "").replace("{}", "")) and \
                        not any(part and norm(part) in norm(en["original"])
                                for part in re.split(r"\.\.\.|\{\.\.\.\}", ep["original"])):
                    row["non_allowlisted"].append(f"edit {i} expanded quotation is a different clause")
                    fail(f"{wid} edit {i}: the expanded quotation shares no retained fragment with "
                         "the abbreviated one — this is substitution, not completion")
                else:
                    row["quotation_expanded"] += 1

            # A4.3 — replacement
            if en.get("replacement") != ep.get("replacement"):
                if (wid, i) not in (fa | fq):
                    row["non_allowlisted"].append(f"edit {i} replacement changed without a validator flag")
                    fail(f"{wid} edit {i}: replacement changed but the validator flagged nothing here")
                else:
                    row["replacement_corrected"] += 1

            # structural consistency of the corrected entry
            act, rep = en.get("action"), (en.get("replacement") or "")
            if act == "removed" and rep.strip():
                fail(f"{wid} edit {i}: action removed must carry an empty replacement")
            if act == "rewritten" and rep.strip() and \
                    en.get("field") in EDITABLE and norm(rep) not in norm(n["spec"].get(en["field"], "")):
                fail(f"{wid} edit {i}: replacement does not exact-match inside the frozen candidate "
                     f"{en['field']} — a replacement may be corrected, never invented")

        rows.append(row)

    tot = {k: sum(r[k] for r in rows) for k in
           ("action_corrected", "quotation_expanded", "replacement_corrected", "provenance_added")}
    tot["tasks_with_non_allowlisted"] = sum(1 for r in rows if r["non_allowlisted"])
    return {"gate": "v2", "anchor_sha256": hashlib.sha256(ANCHOR.read_bytes()).hexdigest(),
            "previous_sha256": hashlib.sha256(PREV.read_bytes()).hexdigest(),
            "flagged_action": len(fa), "flagged_quotation": len(fq),
            "rows": rows, "totals": tot, "hard_failures": hard, "accepted": not hard}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("resubmission", type=Path)
    ap.add_argument("--delta", type=Path)
    a = ap.parse_args()

    res = gate(json.loads(ANCHOR.read_text()), json.loads(PREV.read_text()),
               json.loads(a.resubmission.read_text()))
    t = res["totals"]
    print(f"  validator-flagged entries      action {res['flagged_action']}, "
          f"quotation {res['flagged_quotation']}")
    print(f"  A4.1 actions corrected         {t['action_corrected']}")
    print(f"  A4.2 quotations expanded       {t['quotation_expanded']}")
    print(f"  A4.3 replacements corrected    {t['replacement_corrected']}")
    print(f"  A2   provenance appended       {t['provenance_added']}")
    print(f"  tasks with non-allowlisted change  {t['tasks_with_non_allowlisted']}")
    print()
    for h in res["hard_failures"][:25]:
        print(f"  HARD  {h}")
    if len(res["hard_failures"]) > 25:
        print(f"  … and {len(res['hard_failures']) - 25} more")
    if a.delta:
        a.delta.write_text(json.dumps(res, indent=2, ensure_ascii=False))
        print(f"\nwrote {a.delta}")
    print("\n" + ("IDENTITY GATE v2 PASSED — every change lands in the allowlist.\n"
                  "Now run the frozen writer validator. Both must pass before the hash is frozen."
                  if res["accepted"] else
                  f"IDENTITY GATE v2 FAILED — {len(res['hard_failures'])} non-allowlisted change(s)."))
    sys.exit(0 if res["accepted"] else 1)


if __name__ == "__main__":
    main()
