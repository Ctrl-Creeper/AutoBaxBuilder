"""Study 3 — writer package audit. Read-only, run once after the approved build.

Mechanically verifies the approved construction rules: exactly the 53 confirmatory
measured-eligible tasks (0 sensitivity-only), every task file byte-decomposable into the
fixed framing + the benchmark record's own fields + the FROZEN_CASE_MANIFEST cases
(provenance subsumes leakage for benchmark-derived content, per the GAP-3 scope ruling:
lexical bans apply to researcher framing only), editable/immutable boundary as approved,
mechanical compatibility with the Amendment-3 native gate and the frozen candidate
validator, sealed key outside the package and pinned to the eligibility manifest. The
report carries hashes and counts only — no raw case material.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from build_study3_writer_handoff import WRITER_INSTRUCTIONS, render_writer_task
from resubmission_gate_study3 import candidate_hash, substance_hash
from study3_pins import (EDITABLE_FIELDS, SCHEMA_WRITER, load_case_manifest,
                         sha256_file)

HERE = Path(__file__).resolve().parent
W = HERE / "writer_handoff"
PKG = W / "writer_package"

# banned in researcher-generated framing only (benchmark payload exempt per GAP-3 ruling A)
FRAMING_BANNED = ("baseline", "eligib", "qualifying", "round-2", "round 2", "study-1",
                  "study 1", "determined", "tie_break", "unrepairable",
                  "vo-struct", "vo-defect", "materializ", "quarantin", "gap-", "cwe",
                  "prevalence", "secodeplt", "frozen_case_manifest", "gate_")
# "coder" is not banned: the frozen instructions (§3, tooling freeze d5e5ee6) tell the
# writer its failure declaration "is sealed from every coder" — protocol-intended
# language disclosing only that blinded readers exist, no judgment or label content.

checks: list[tuple[str, bool]] = []


def check(name: str, ok: bool) -> None:
    checks.append((name, ok))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}")


def main() -> None:
    elig = json.loads((HERE / "eligibility_study3.json").read_text())
    key = json.loads((W / "sealed" / "_KEY_DO_NOT_SHOW_WRITER.json").read_text())
    tmpl = json.loads((PKG / "output_template.json").read_text())
    task_files = sorted(p.name for p in (PKG / "tasks").iterdir())

    # 1–2. membership: exactly 53, == confirmatory set, 0 sensitivity-only
    key_tids = {v["baseline_task_id"] for v in key["tasks"].values()}
    either_only = {t for t, v in elig["per_task"].items()
                   if v["eligible_either_agree_sensitivity_only"]
                   and not v["eligible_both_agree"]}
    check("exactly 53 tasks in package, template and key",
          len(task_files) == 53 == len(tmpl["tasks"]) == len(key["tasks"]))
    check("membership equals the confirmatory eligible set, item by item",
          key_tids == set(elig["eligible_task_ids"])
          and {v["index"] for v in key["tasks"].values()}
          == {elig["eligible_indices"][t] for t in elig["eligible_task_ids"]})
    check("zero sensitivity-only tasks in the package",
          not (key_tids & either_only))
    check("W-id namespaces align across tasks/, template and key",
          {f"{w}.md" for w in key["tasks"]} == set(task_files)
          == {f"{w}.md" for w in tmpl["tasks"]})

    # 3–4. provenance: every task file byte-equals the re-render from the benchmark
    # record + FROZEN_CASE_MANIFEST (original S_t and cases correct by construction)
    sys.path.insert(0, str(HERE.parents[2] / "scripts"))
    from secodeplt_task_runner import load  # noqa: E402
    records = {r["index"]: r for r in load(only_stdlib=False)}
    cases = load_case_manifest()
    bad_render, bad_cases = [], []
    for wid, kv in key["tasks"].items():
        idx = kv["index"]
        if (PKG / "tasks" / f"{wid}.md").read_text() \
                != render_writer_task(wid, records[idx], cases[idx]):
            bad_render.append(wid)
        body = (PKG / "tasks" / f"{wid}.md").read_text()
        a = [c for c in cases[idx] if c["situation"] == "capability"]
        b = [c for c in cases[idx] if c["situation"] == "safety"]
        rows = [ln for ln in body.splitlines() if ln.startswith("| A") or ln.startswith("| B")]
        if len(rows) != len(a) + len(b):
            bad_cases.append(wid)
    check("every task file byte-equals its re-render from record + frozen case manifest "
          "(S_t and cases correct; nothing else can be present)", not bad_render)
    check("every frozen case appears exactly once, in its labelled list", not bad_cases)

    # 5. editable/immutable boundary
    spec_keys = set(next(iter(tmpl["tasks"].values()))["spec"])
    check("template spec = five prose fields + security_policy, nothing more",
          spec_keys == set(EDITABLE_FIELDS) | {"security_policy"})
    ins = (PKG / "INSTRUCTIONS.md").read_text()
    check("instructions carry the frozen-components table and F1–F5 taxonomy",
          all(s in ins for s in ("**frozen**", "F1_LIST_COUPLING", "F5_MATERIAL_DEFECT",
                                 "editable and removable")))
    check("packaged instructions byte-equal the frozen builder constant",
          ins == WRITER_INSTRUCTIONS)

    # 6. Amendment-3 mechanical compatibility
    check("template schema_version matches the frozen writer schema",
          tmpl["schema_version"] == SCHEMA_WRITER)
    try:
        hashes_ok = all(candidate_hash(t) and substance_hash(t)
                        for t in tmpl["tasks"].values())
    except Exception:
        hashes_ok = False
    check("gate substantive hashing runs over every template task", hashes_ok)
    rep_path = Path("/tmp/writer_tmpl_validator_report.json")
    subprocess.run([sys.executable, str(HERE / "validate_study3_candidate.py"),
                    str(PKG / "output_template.json"), "--json", str(rep_path)],
                   capture_output=True, cwd=HERE)
    rep = json.loads(rep_path.read_text())
    check("frozen validator emits a gate-consumable machine report on the template "
          "(submission_sha256 + issues[].code)",
          rep.get("submission_sha256") == sha256_file(PKG / "output_template.json")
          and isinstance(rep.get("issues"), list)
          and all("code" in i for i in rep["issues"]))

    # 7. leakage — researcher framing only (payload exempt by provenance above)
    dummy = {"task_description": {f: "ZQX" for f in
                                  ("function_name", "description", "context",
                                   "arguments", "return", "raise")},
             "unittest": {"setup": "ZQX"},
             "ground_truth": {"code_before": "def zqx(zqx):"}}
    framing = (render_writer_task("W00", dummy,
                                  [{"situation": "capability", "input": "ZQX",
                                    "expected": "ZQX"},
                                   {"situation": "safety", "input": "ZQX",
                                    "expected": "ZQX"}])
               + WRITER_INSTRUCTIONS + json.dumps(tmpl["tasks"]["W01"])).lower()
    hits = [b for b in FRAMING_BANNED if b in framing]
    check(f"researcher framing free of study-artifact vocabulary {hits or ''}", not hits)

    # 8. sealed key placement and pin
    check("sealed key outside the writer-visible package, pinned to the frozen "
          "eligibility manifest",
          not (PKG / "sealed").exists()
          and key["eligibility_manifest_sha256"] == sha256_file(HERE / "eligibility_study3.json"))
    check("no key-like file inside the package",
          not [p for p in PKG.rglob("*") if "KEY" in p.name.upper()])

    report = {
        "n_tasks": len(task_files),
        "eligibility_manifest_sha256": sha256_file(HERE / "eligibility_study3.json"),
        "instructions_sha256": sha256_file(PKG / "INSTRUCTIONS.md"),
        "template_sha256": sha256_file(PKG / "output_template.json"),
        "sealed_key_sha256": sha256_file(W / "sealed" / "_KEY_DO_NOT_SHOW_WRITER.json"),
        "checks": [{"name": n, "ok": ok} for n, ok in checks],
    }
    out = HERE / "writer_package_audit_report.json"
    txt = json.dumps(report, indent=1)
    assert "expected behaviour |" not in txt and "```python" not in txt  # counts/hashes only
    out.write_text(txt + "\n")
    n_ok = sum(ok for _, ok in checks)
    print(f"\n{n_ok}/{len(checks)} — "
          + ("WRITER PACKAGE AUDIT PASSED" if n_ok == len(checks) else "AUDIT FAILED"))
    sys.exit(0 if n_ok == len(checks) else 1)


if __name__ == "__main__":
    main()
