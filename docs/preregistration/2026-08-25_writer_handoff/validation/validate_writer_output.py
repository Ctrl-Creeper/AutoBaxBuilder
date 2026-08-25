"""Validate a writer submission against the frozen contract.

**This validator does not judge specifications.** It never asks whether a candidate
is functionally sufficient, whether it leaves anything open, or whether it is any
good. Those are the constructs the blinded coding runs exist to measure; deciding
them here would write the result into the data-generating process.

What it checks is delivery: that ninety candidates arrived, that each traces to its
frozen input, that nothing outside the editable fields moved, and that every
difference between the original prose and the candidate is accounted for by a
declared edit.

Two tiers, and the difference is enforced, not merely documented:

  HARD        procedural invariants. Any failure means the submission is not
              accepted — a submission-format or provenance error, returned to the
              writer. Exit code 1.
  DIAGNOSTIC  distributional observations. Printed, never acted on. A diagnostic
              may not cause a task to be edited, dropped, replaced or re-authored,
              and never changes the exit code.

Usage:
    validate_writer_output.py <writer_output.json> [--package DIR] [--json OUT]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

SCHEMA_VERSION = "round2-writer-v1"
EDITABLE = ("description", "context", "arguments", "return", "raise")
DROPPED = "security_policy"
FAILURE_CODES = {"F1_LIST_COUPLING", "F2_SIGNATURE_CARRIER", "F3_PREAMBLE_CARRIER",
                 "F4_RETURN_CONTRACT_CARRIER", "F5_MATERIAL_DEFECT"}
TASK_KEYS = {"spec", "edits", "sufficiency_evidence", "failure", "notes"}
EDIT_KEYS = {"field", "original", "action", "replacement", "why"}
# Vocabulary that belongs to the coding side. The writer classifies nothing, so
# its appearance means the roles have blurred.
CODER_VOCAB = re.compile(r"\bSEPARABLE\b|\bINSEPARABLE\b|STRUCTURALLY[ _-]?CARRIED|"
                         r"NOT[ _-]?YET[ _-]?BLINDED|OVER[ _-]?STRIPPED|\bdetermined\b.{0,20}\bclass",
                         re.I)

HANDOFF = Path(__file__).resolve().parent.parent
REPO_SEL = Path("docs/preregistration/2026-08-25_round2_selection/round2_selection.json")

hard: list[str] = []
diag: list[str] = []


def fail(msg: str) -> None:
    hard.append(msg)


def note(msg: str) -> None:
    diag.append(msg)


def sentences(text: str) -> list[str]:
    """Coarse clause split. Used only to locate text, never to interpret it."""
    return [s.strip() for s in re.split(r"(?<=[.;:])\s+|\n+", text or "") if s.strip()]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def parse_original(md: str) -> dict[str, str]:
    """Recover the original prose fields from a frozen task file."""
    out = {}
    for label, key in (("Description", "description"), ("Context", "context"),
                       ("Arguments", "arguments"), ("Return", "return"),
                       ("Raise", "raise"), ("Security Policy", DROPPED)):
        m = re.search(rf"^\*\*{re.escape(label)}:\*\* (.*?)(?=\n\*\*|\n## )", md, re.S | re.M)
        out[key] = m.group(1).strip() if m else ""
    return out


def check_package_integrity(pkg_dir: Path) -> None:
    """The non-editable material must still be exactly what was frozen."""
    mf_path = HANDOFF / "writer_package_manifest.json"
    if not mf_path.exists():
        fail("frozen package manifest not found; package integrity cannot be established")
        return
    mf = json.loads(mf_path.read_text())
    live = {}
    for p in sorted(pkg_dir.rglob("*")):
        if p.is_file():
            live[f"writer_package/{p.relative_to(pkg_dir)}"] = hashlib.sha256(p.read_bytes()).hexdigest()
    if live != mf["files"]:
        changed = sorted(set(live) ^ set(mf["files"])) or \
            [k for k in live if mf["files"].get(k) != live[k]]
        fail(f"package no longer matches the frozen manifest — non-editable material moved: {changed[:5]}")
    if REPO_SEL.exists():
        if hashlib.sha256(REPO_SEL.read_bytes()).hexdigest() != mf["selection_sha256"]:
            fail("the frozen selection file has changed since the package was built")


def validate(sub_path: Path, pkg_dir: Path) -> dict:
    sub = json.loads(sub_path.read_text())

    if sub.get("schema_version") != SCHEMA_VERSION:
        fail(f"schema_version is {sub.get('schema_version')!r}, expected {SCHEMA_VERSION!r}")
    if not (sub.get("writer_id") or "").strip():
        fail("writer_id is empty")

    check_package_integrity(pkg_dir)

    inputs = {p.stem: parse_original(p.read_text()) for p in sorted((pkg_dir / "tasks").glob("W*.md"))}
    if len(inputs) != 90:
        fail(f"the frozen package holds {len(inputs)} task inputs, expected 90")

    tasks = sub.get("tasks")
    if not isinstance(tasks, dict):
        fail("tasks is missing or not an object")
        return summarise()

    missing = sorted(set(inputs) - set(tasks))
    unknown = sorted(set(tasks) - set(inputs))
    if missing:
        fail(f"{len(missing)} task(s) absent from the submission: {missing[:6]} — "
             "a task may never be dropped, a failure code is recorded instead")
    if unknown:
        fail(f"submission contains ids with no frozen input: {unknown[:6]}")

    lens, edits_per_task, codes, empties = [], [], [], 0

    for wid in sorted(set(inputs) & set(tasks)):
        orig, t = inputs[wid], tasks[wid]
        where = f"{wid}"

        if not isinstance(t, dict) or set(t) != TASK_KEYS:
            fail(f"{where}: keys are {sorted(t) if isinstance(t, dict) else type(t).__name__}, "
                 f"expected exactly {sorted(TASK_KEYS)} — missing keys are an error, not a default")
            continue

        spec = t["spec"]
        if not isinstance(spec, dict) or set(spec) != set(EDITABLE):
            fail(f"{where}: spec keys are {sorted(spec) if isinstance(spec, dict) else '?'}, "
                 f"expected exactly the five editable fields")
            continue
        if DROPPED in spec or any(DROPPED in str(k).lower() for k in spec):
            fail(f"{where}: {DROPPED} must not appear in the candidate")

        for f in EDITABLE:
            if not isinstance(spec[f], str):
                fail(f"{where}: spec.{f} is not a string")

        # --- failure record
        fr = t["failure"]
        if fr is not None:
            if not isinstance(fr, dict) or set(fr) != {"code", "at_case", "detail"}:
                fail(f"{where}: failure must be null or have exactly code/at_case/detail")
            elif fr["code"] not in FAILURE_CODES:
                fail(f"{where}: failure code {fr['code']!r} is not in the frozen taxonomy")
            else:
                codes.append(fr["code"])
            if not any((spec.get(f) or "").strip() for f in EDITABLE):
                fail(f"{where}: a failure was recorded and the candidate is empty — "
                     "a failure never removes the obligation to submit a best candidate")

        # --- edit provenance: declared edits must be locatable in the original
        if not isinstance(t["edits"], list):
            fail(f"{where}: edits is not a list")
            continue
        for n, e in enumerate(t["edits"], 1):
            if not isinstance(e, dict) or set(e) != EDIT_KEYS:
                fail(f"{where} edit {n}: keys are {sorted(e) if isinstance(e, dict) else '?'}, "
                     f"expected exactly {sorted(EDIT_KEYS)}")
                continue
            if e["field"] not in (*EDITABLE, DROPPED):
                fail(f"{where} edit {n}: field {e['field']!r} is not an original prose field")
                continue
            if e["action"] not in ("removed", "rewritten"):
                fail(f"{where} edit {n}: action {e['action']!r} is not removed or rewritten")
            if norm(e["original"]) and norm(e["original"]) not in norm(orig.get(e["field"], "")):
                fail(f"{where} edit {n}: the quoted original is not present in the frozen "
                     f"{e['field']} field — provenance is not traceable")
            if e["action"] == "removed" and norm(e["replacement"]):
                fail(f"{where} edit {n}: action is removed but a replacement is given")
            if e["action"] == "rewritten":
                if not norm(e["replacement"]):
                    fail(f"{where} edit {n}: action is rewritten but no replacement is given")
                elif e["field"] in EDITABLE and norm(e["replacement"]) not in norm(spec[e["field"]]):
                    fail(f"{where} edit {n}: the replacement does not appear in the candidate "
                         f"{e['field']} — original to candidate is not traceable")

        # --- the converse: every clause that vanished must be declared
        declared = [norm(e["original"]) for e in t["edits"] if isinstance(e, dict) and "original" in e]
        for f in EDITABLE:
            for s in sentences(orig.get(f, "")):
                if norm(s) and norm(s) not in norm(spec[f]):
                    if not any(d and (norm(s) in d or d in norm(s)) for d in declared):
                        fail(f"{where}: a clause of the original {f} is absent from the candidate "
                             f"with no edit declaring it: {s[:70]!r}")

        # --- role boundary
        blob = json.dumps(t, ensure_ascii=False)
        if CODER_VOCAB.search(blob):
            fail(f"{where}: contains coding-side classification vocabulary "
                 f"({set(CODER_VOCAB.findall(blob))}) — the writer classifies nothing")

        if not isinstance(t["sufficiency_evidence"], list):
            fail(f"{where}: sufficiency_evidence is not a list")
        if not isinstance(t["notes"], str):
            fail(f"{where}: notes is not a string")

        # --- diagnostics: observed, never acted on
        o_len = sum(len(orig.get(f, "")) for f in EDITABLE)
        c_len = sum(len(spec.get(f, "")) for f in EDITABLE)
        lens.append((wid, o_len, c_len))
        edits_per_task.append(len(t["edits"]))
        empties += sum(1 for f in EDITABLE if not (spec.get(f) or "").strip())

    if lens:
        ratios = [c / o for _, o, c in lens if o]
        note(f"candidate/original prose length ratio: median {statistics.median(ratios):.2f}, "
             f"min {min(ratios):.2f}, max {max(ratios):.2f}")
        shrunk = [w for w, o, c in lens if o and c / o < 0.4]
        note(f"tasks whose prose shrank below 40% of the original: {len(shrunk)} {shrunk[:8]}")
    if edits_per_task:
        note(f"edits per task: median {statistics.median(edits_per_task):.1f}, "
             f"max {max(edits_per_task)}, tasks with none {edits_per_task.count(0)}")
    note(f"empty editable fields across the submission: {empties}")
    note(f"failure codes recorded: {dict(Counter(codes)) or 'none'}")

    return summarise()


def summarise() -> dict:
    return {"hard_failures": hard, "diagnostics": diag,
            "accepted": not hard}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("submission", type=Path)
    ap.add_argument("--package", type=Path, default=HANDOFF / "writer_package")
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()

    res = validate(a.submission, a.package)

    for d in res["diagnostics"]:
        print(f"  diagnostic  {d}")
    print()
    for h in res["hard_failures"]:
        print(f"  HARD  {h}")

    if res["accepted"]:
        digest = hashlib.sha256(a.submission.read_bytes()).hexdigest()
        print(f"\nACCEPTED — {len(res['diagnostics'])} diagnostics, 0 hard failures")
        print(f"submission sha256: {digest}")
        print("Freeze this hash and commit before any packet is built from the output.")
        res["submission_sha256"] = digest
    else:
        print(f"\nNOT ACCEPTED — {len(res['hard_failures'])} hard failure(s). "
              "Return to the writer as a submission-format or provenance error.")
        print("Diagnostics above are observations only and are not grounds for editing, "
              "dropping or replacing any task.")

    if a.json:
        a.json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(0 if res["accepted"] else 1)


if __name__ == "__main__":
    main()
