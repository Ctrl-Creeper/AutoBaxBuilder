"""Post-build audit of the formal Study-3 baseline packets. Read-only.

Every check recomputes from the pinned sources — frozen protocol (seed derivation), frozen
frame, frozen selection manifest (hash-pinned), benchmark records, shipped get_prompt, and
the sealed FROZEN_CASE_MANIFEST — and compares against what the builder wrote. No
submission exists yet; nothing here reads a judgement, derives eligibility, or invokes the
scorer.

GAP-3 Amendment 2 (clause 9): the former "fresh extraction must byte-equal packet cases"
invariant is superseded. The invariant checked here is
    packet case object ≡ FROZEN_CASE_MANIFEST case object
byte-for-byte. This audit never re-executes testcase extraction (clause 8); a manifest
mismatch is a hard stop and never a trigger for rematerialization (clause 10).

Scan-scope rule (FAIL-2 ruling, 2026-08-28): the lexical banned-token scan applies to
RESEARCHER-GENERATED material only — instructions, templates, fingerprints, filenames, and
the builder-added framing of task files. Benchmark-derived payload (the S block between the
sentinel markers, and the case-table cells) is exempt from lexical scanning: it is shown by
design, and benchmark vocabulary is not study leakage. As compensation the audit carries a
mechanical PROVENANCE check: every task file must byte-decompose into exactly (fixed
render_task template) + (shipped get_prompt output) + (case cells whose inputs equal the
frozen extractor's fresh output) — so the exempt payload can only originate from the
protocol-allowed benchmark/extractor paths, and nothing else can hide inside the exemption.
No per-hit manual exception mechanism exists. Documented schema-identifier note: the string
`study3-baseline-run-v1` in answers_template.json follows the frozen Study-1 precedent
(`study1-run-v1` was likewise coder-visible).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from study3_pins import (FRAME, FRAME_SHA, PROTOCOL_SHA, RUNS,  # noqa: E402
                         SCHEMA_BASELINE, SEED_SLICES, load_case_manifest, sha256_file)
from select_study3_sample import draw  # noqa: E402
from packet_build import (BEGIN_S, END_S,  # noqa: E402
                          load_shipped_get_prompt, render_task)
from validate_study3_submission import J1_KEYS, TASK_KEYS  # noqa: E402

SELECTION = HERE / "selection_study3.json"
SELECTION_SHA = "b194696cdf54b94dfad4e4a213314a6fadb081876e94565708bb4ea64984bab3"
BASE = HERE / "baseline"

fails: list[str] = []
report: dict = {}


def check(ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {msg}")
    if not ok:
        fails.append(msg)


def main() -> None:  # noqa: C901
    # --- input pins unchanged
    check(sha256_file(SELECTION) == SELECTION_SHA, "selection manifest matches frozen hash")
    check(sha256_file(FRAME) == FRAME_SHA, "frame matches frozen hash")
    manifest = json.loads(SELECTION.read_text())
    check(manifest["protocol_sha256"] == PROTOCOL_SHA and manifest["seed"] == 1418386877,
          "manifest pins the frozen protocol hash and seed 1418386877")

    # --- draw re-derived from frozen seed + frame, item-equal to the manifest
    frame_doc = json.loads(FRAME.read_text())
    rederived = draw(frame_doc["frame"], int(PROTOCOL_SHA[0:8], 16), 90)
    check(rederived == manifest["selection"],
          "90-task draw re-derives item-equal from frozen seed + frame")
    selection = manifest["selection"]

    key = json.loads((BASE / "sealed/_KEY_DO_NOT_SHOW_CODERS.json").read_text())

    # --- exactly the frozen 90, no substitution
    key_indices = sorted(v["index"] for v in key["tasks"].values())
    check(len(key["tasks"]) == 90, "exactly 90 tasks in the key")
    check(key_indices == sorted(selection), "key indices are exactly the frozen selection")
    check(key["selection_manifest_sha256"] == SELECTION_SHA,
          "key pins the frozen selection manifest hash")

    # --- seeds and task assignment reproducible from the protocol hash
    seeds = {"task_order": int(PROTOCOL_SHA[slice(*SEED_SLICES["baseline_task_order"])], 16),
             "run1": int(PROTOCOL_SHA[slice(*SEED_SLICES["baseline_run1_cases"])], 16),
             "run2": int(PROTOCOL_SHA[slice(*SEED_SLICES["baseline_run2_cases"])], 16)}
    check(key["seeds"] == seeds, "key seeds equal the protocol-derived slice values")
    check(seeds["task_order"] != 1418386877 and 1418386877 not in
          (seeds["run1"], seeds["run2"]),
          "presentation seeds are disjoint from the [0:8] selection seed")
    order = np.random.default_rng(seeds["task_order"]).permutation(len(selection))
    assign = {f"P{p:02d}": selection[int(i)] for p, i in enumerate(order, 1)}
    check({t: m["index"] for t, m in key["tasks"].items()} == assign,
          "task-id assignment reproduces from the task_order seed")

    from secodeplt_task_runner import load
    records = {r["index"]: r for r in load(only_stdlib=False)}
    get_prompt = load_shipped_get_prompt()  # byte-verifies instruct.py against its pin

    # --- frozen case manifest: pinned in the key, sole case source (Amendment 2)
    manifest_sha = sha256_file(HERE / "sealed_materialization/FROZEN_CASE_MANIFEST.json")
    check(key.get("frozen_case_manifest_sha256") == manifest_sha,
          "key pins the sealed FROZEN_CASE_MANIFEST hash")
    cases_by_index = load_case_manifest()  # verifies against SHA256SUMS_MATERIALIZATION
    check(sorted(cases_by_index) == sorted(selection),
          "manifest covers exactly the frozen selection")

    # --- per-task recomputation: S_t, manifest cases, permutations, file byte-equality
    n_bad_s = n_bad_cases = n_bad_perm = n_bad_file = 0
    rngs = {run: np.random.default_rng(seeds[run]) for run in RUNS}
    for tid in sorted(assign):
        rec = records[assign[tid]]
        s_t = get_prompt(rec)
        cases = cases_by_index[assign[tid]]
        meta = key["tasks"][tid]
        if [c["situation"] for c in cases] != meta["case_situations_source_order"]:
            n_bad_cases += 1
        for run in RUNS:
            want_order = [int(i) for i in rngs[run].permutation(len(cases))]
            if want_order != meta[f"{run}_case_order"]:
                n_bad_perm += 1
            md = (BASE / f"{run}_package/tasks/{tid}.md").read_text()
            if md.split(BEGIN_S, 1)[1].split(END_S, 1)[0].strip() != s_t:
                n_bad_s += 1
            if md != render_task(tid, s_t, cases, meta[f"{run}_case_order"]):
                n_bad_file += 1
    check(n_bad_s == 0, "every packet S block is byte-identical to shipped get_prompt output "
                        "(90 tasks × 2 packages)")
    check(n_bad_cases == 0, "manifest case situations match the key for all tasks")
    check(n_bad_perm == 0, "all 180 case permutations reproduce from the protocol-derived seeds")
    check(n_bad_file == 0, "every task file is byte-identical to a re-rendering from "
                           "get_prompt + FROZEN_CASE_MANIFEST (the Amendment-2 invariant)")

    # --- canonical payload recomputed from the package files themselves
    payload = {}
    for run in RUNS:
        canon = {}
        for tid in sorted(assign):
            md = (BASE / f"{run}_package/tasks/{tid}.md").read_text()
            block = md.split(BEGIN_S, 1)[1].split(END_S, 1)[0].strip()
            rows = re.findall(r"^\| \d+ \| `(.*)` \| `(.*)` \|$", md, re.MULTILINE)
            canon[tid] = {"s_t": block, "cases": sorted([a, b] for a, b in rows)}
        payload[run] = hashlib.sha256(
            json.dumps(canon, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    check(payload["run1"] == payload["run2"],
          "canonical semantic payload recomputed from files is identical across runs")
    check(payload["run1"] == key["canonical_payload_sha256"]["run1"],
          "recomputed payload hash equals the one sealed in the key")
    n_cases = sum(len(v["case_situations_source_order"]) for v in key["tasks"].values())
    n_rows = {run: sum(len(re.findall(r"^\| \d+ \|",
                                      (BASE / f"{run}_package/tasks/{t}.md").read_text(),
                                      re.MULTILINE)) for t in sorted(assign))
              for run in RUNS}
    n_manifest = sum(len(cases_by_index[i]) for i in selection)
    check(n_rows["run1"] == n_rows["run2"] == n_cases == n_manifest == 394,
          f"each of the manifest's 394 cases appears exactly once per run "
          f"(rows {n_rows['run1']}/{n_rows['run2']}, key {n_cases}, manifest {n_manifest})")

    # --- packages differ only in presentation
    same = all((BASE / f"run1_package/{f}").read_bytes() ==
               (BASE / f"run2_package/{f}").read_bytes()
               for f in ("INSTRUCTIONS.md", "answers_template.json", "PACKET_FINGERPRINT"))
    check(same, "instructions, template and fingerprint are byte-identical across packages")

    # --- coder-visible RESEARCHER-GENERATED material: no labels, mappings, or
    #     foreign-study/outcome traces. Benchmark-derived payload (S block, case cells)
    #     is exempt from the lexical scan; its provenance is proven mechanically below.
    hard_banned = ["writer", "round2", "round-2", "secodeplt", "selection", "_KEY_",
                   "sealed", "study1", "study-1", "prevalence", "eligib",
                   "materializ", "manifest", "amendment", "gap-3", "gap3", "quarantin",
                   "host_resource", "frozen_case", "provenance"]
    hard_patterns = [r"\bJ2\b", r"\bJ3\b", r"\bDS\b", r"\bVO\b", r"\bUR\b"]
    label_banned = ["capability", "safety"]
    leaks = []
    for run in RUNS:
        other = "run2" if run == "run1" else "run1"
        for p in sorted((BASE / f"{run}_package").rglob("*")):
            if not p.is_file():
                continue
            text = p.read_text()
            if p.parent.name == "tasks":
                framing = text.split(BEGIN_S, 1)[0] + text.split(END_S, 1)[1]
                framing = re.sub(r"^\| \d+ \|.*$", "", framing, flags=re.MULTILINE)
            else:
                framing = text
            framing += f"\n{p.name}"  # filenames are researcher-generated too
            low = framing.lower()
            leaks += [f"{run}/{p.name}: {w}" for w in hard_banned + [other] + label_banned
                      if w in low]
            leaks += [f"{run}/{p.name}: {pat}" for pat in hard_patterns
                      if re.search(pat, framing)]
    check(not leaks, "no banned token in researcher-generated coder-visible material "
                     f"(hits: {leaks[:6] or 'none'})")

    # --- provenance of the lexically-exempt payload: each task file must byte-decompose
    #     into the fixed template + shipped get_prompt output + case cells byte-equal to
    #     the FROZEN_CASE_MANIFEST objects. Nothing else can occupy the exemption.
    n_bad_prov = 0
    for tid in sorted(assign):
        rec = records[assign[tid]]
        s_t = get_prompt(rec)
        want_cells = [[c["input"], c["expected"]] for c in cases_by_index[assign[tid]]]
        meta = key["tasks"][tid]
        for run in RUNS:
            md = (BASE / f"{run}_package/tasks/{tid}.md").read_text()
            rows = re.findall(r"^\| \d+ \| `(.*)` \| `(.*)` \|$", md, re.MULTILINE)
            order = meta[f"{run}_case_order"]
            if len(rows) != len(order):
                n_bad_prov += 1
                continue
            cells_src = [None] * len(order)
            for pos, o in enumerate(order):
                cells_src[o] = [rows[pos][0], rows[pos][1]]
            cases_src = [{"input": a, "expected": b} for a, b in cells_src]
            if md != render_task(tid, s_t, cases_src, order) or cells_src != want_cells:
                n_bad_prov += 1
    check(n_bad_prov == 0,
          "exempt payload provenance: every task file byte-decomposes into template + "
          "get_prompt output + manifest case cells (inputs AND expected byte-equal)")

    # --- sealed key lives outside both packages
    inside = [str(p) for run in RUNS
              for p in (BASE / f"{run}_package").rglob("*") if "KEY" in p.name.upper()]
    check(not inside and (BASE / "sealed/_KEY_DO_NOT_SHOW_CODERS.json").exists(),
          "sealed key exists and no key-like file sits inside a package")

    # --- blank template conforms to the frozen validator's schema; no answers simulated
    tmpl = json.loads((BASE / "run1_package/answers_template.json").read_text())
    check(tmpl["schema_version"] == SCHEMA_BASELINE
          and set(tmpl) == {"schema_version", "coder_id", "packet_fingerprint_sha256", "tasks"}
          and all(set(t) == TASK_KEYS and all(set(e) == J1_KEYS for e in t["J1"])
                  for t in tmpl["tasks"].values())
          and all(len(tmpl["tasks"][tid]["J1"]) ==
                  len(key["tasks"][tid]["case_situations_source_order"])
                  for tid in key["tasks"]),
          "blank template matches the frozen validator schema and the key's case counts")
    r = subprocess.run([sys.executable, str(HERE / "validate_study3_submission.py"),
                        str(BASE / "run1_package/answers_template.json"),
                        "--package", str(BASE / "run1_package")],
                       capture_output=True, text=True)
    structural = any(s in r.stdout for s in ("keys are", "case numbers", "task(s) absent",
                                             "no counterpart", "entries,"))
    blank_only = ("not recorded as a boolean" in r.stdout and "confidence" in r.stdout)
    check(r.returncode == 1 and blank_only and not structural,
          "frozen validator rejects the blank template for blankness only, never structure")

    report.update({"protocol_sha256": PROTOCOL_SHA, "selection_sha256": SELECTION_SHA,
                   "frame_sha256": FRAME_SHA, "seeds": seeds,
                   "n_tasks": 90, "n_cases": n_cases,
                   "canonical_payload_sha256": payload, "checks_failed": fails})
    (HERE / "baseline_packet_audit_report.json").write_text(json.dumps(report, indent=2))
    print(f"\n{'PACKET AUDIT PASSED' if not fails else str(len(fails)) + ' FAILURE(S)'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
