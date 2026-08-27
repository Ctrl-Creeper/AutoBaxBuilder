"""Post-build audit of the formal Study-1 run packets. Read-only.

Every check recomputes from the pinned sources (selection manifest, benchmark
records, shipped get_prompt, protocol-derived seeds) and compares against what the
builder wrote. Nothing here reads a judgement — no submissions exist yet — and the
scorer is not invoked.

Scan-scope note for the coder-visible check: the S_t block and the case table are
benchmark content, shown by design (the estimand is the benchmark as shipped), so
the case-kind words are scanned only over the builder-added framing outside both.
Artifact names that can never legitimately appear (writer, round2, secodeplt,
selection, the other run's name) are scanned over entire files.
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
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "scripts"))

from build_study1_packets import (BEGIN_S, END_S, PROTOCOL_SHA, SELECTION,  # noqa: E402
                                  SELECTION_SHA, extract_cases, load_shipped_get_prompt,
                                  render_task)
from validate_study1_submission import J1_KEYS, SCHEMA_VERSION, TASK_KEYS  # noqa: E402

RUNS = ("run1", "run2")
fails: list[str] = []
report: dict = {}


def check(ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {msg}")
    if not ok:
        fails.append(msg)


def main() -> None:  # noqa: C901
    if hashlib.sha256(SELECTION.read_bytes()).hexdigest() != SELECTION_SHA:
        sys.exit("selection manifest hash mismatch; stopping, not patching")
    selection = json.loads(SELECTION.read_text())["selection"]
    key = json.loads((HERE / "sealed/_KEY_DO_NOT_SHOW_CODERS.json").read_text())

    # --- exactly the frozen 90, no substitution, no reserve promotion
    key_indices = sorted(v["index"] for v in key["tasks"].values())
    check(len(key["tasks"]) == 90, "exactly 90 tasks in the key")
    check(key_indices == sorted(selection), "key indices are exactly the frozen selection")

    # --- seeds and task assignment reproducible from the protocol hash
    seeds = {"task_order": int(PROTOCOL_SHA[0:8], 16),
             "run1_cases": int(PROTOCOL_SHA[8:16], 16),
             "run2_cases": int(PROTOCOL_SHA[16:24], 16)}
    check(key["seeds"] == seeds, "key seeds equal the protocol-derived values")
    order = np.random.default_rng(seeds["task_order"]).permutation(len(selection))
    assign = {f"P{p:02d}": selection[int(i)] for p, i in enumerate(order, 1)}
    check({t: m["index"] for t, m in key["tasks"].items()} == assign,
          "task-id assignment reproduces from the task_order seed")

    from secodeplt_task_runner import load
    records = {r["index"]: r for r in load(only_stdlib=False)}
    get_prompt = load_shipped_get_prompt()

    # --- per-task recomputation: S_t, cases, permutations, full file byte-equality
    n_bad_s = n_bad_cases = n_bad_perm = n_bad_file = 0
    rngs = {run: np.random.default_rng(seeds[f"{run}_cases"]) for run in RUNS}
    for tid in sorted(assign):
        rec = records[assign[tid]]
        s_t = get_prompt(rec)
        cases = extract_cases(rec)
        meta = key["tasks"][tid]
        if [c["situation"] for c in cases] != meta["case_situations_source_order"]:
            n_bad_cases += 1
        for run in RUNS:
            want_order = [int(i) for i in rngs[run].permutation(len(cases))]
            if want_order != meta[f"{run}_case_order"]:
                n_bad_perm += 1
            md = (HERE / f"{run}_package/tasks/{tid}.md").read_text()
            if md.split(BEGIN_S, 1)[1].split(END_S, 1)[0].strip() != s_t:
                n_bad_s += 1
            if md != render_task(tid, s_t, cases, meta[f"{run}_case_order"]):
                n_bad_file += 1
    check(n_bad_s == 0, "every packet S block is byte-identical to shipped get_prompt output "
                        "(90 tasks × 2 packages)")
    check(n_bad_cases == 0, "fresh case extraction matches the key's situations for all tasks")
    check(n_bad_perm == 0, "all 180 case permutations reproduce from the protocol-derived seeds")
    check(n_bad_file == 0, "every task file is byte-identical to a from-source re-rendering")

    # --- canonical payload recomputed from the package files themselves
    payload = {}
    for run in RUNS:
        canon = {}
        for tid in sorted(assign):
            md = (HERE / f"{run}_package/tasks/{tid}.md").read_text()
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
    n_rows = sum(len(re.findall(r"^\| \d+ \|", (HERE / f"run1_package/tasks/{t}.md").read_text(),
                                re.MULTILINE)) for t in sorted(assign))
    check(n_rows == n_cases == 442, f"case tables carry each case exactly once ({n_rows} rows)")

    # --- packages differ only in presentation
    same = all((HERE / f"run1_package/{f}").read_bytes() == (HERE / f"run2_package/{f}").read_bytes()
               for f in ("INSTRUCTIONS.md", "answers_template.json", "PACKET_FINGERPRINT"))
    check(same, "instructions, template and fingerprint are byte-identical across packages")

    # --- coder-visible material carries no labels, mappings, or foreign-study traces
    hard_banned = ["writer", "round2", "round-2", "secodeplt", "selection",
                   "_KEY_", "sealed"]
    label_banned = ["capability", "safety"]
    leaks = []
    for run in RUNS:
        other = "run2" if run == "run1" else "run1"
        for p in sorted((HERE / f"{run}_package").rglob("*")):
            if not p.is_file():
                continue
            text = p.read_text()
            low = text.lower()
            leaks += [f"{run}/{p.name}: {w}" for w in hard_banned + [other] if w in low]
            if p.parent.name == "tasks":
                framing = text.split(BEGIN_S, 1)[0] + text.split(END_S, 1)[1]
                framing = re.sub(r"^\| \d+ \|.*$", "", framing, flags=re.MULTILINE)
            else:
                framing = text
            leaks += [f"{run}/{p.name}: {w}" for w in label_banned if w in framing.lower()]
    check(not leaks, f"no banned token in coder-visible material (hits: {leaks[:6] or 'none'})")

    # --- sealed key lives outside both packages
    inside = [str(p) for run in RUNS
              for p in (HERE / f"{run}_package").rglob("*") if "KEY" in p.name.upper()]
    check(not inside and (HERE / "sealed/_KEY_DO_NOT_SHOW_CODERS.json").exists(),
          "sealed key exists and no key-like file sits inside a package")

    # --- blank template conforms to the frozen validator's schema; no answers simulated
    tmpl = json.loads((HERE / "run1_package/answers_template.json").read_text())
    check(tmpl["schema_version"] == SCHEMA_VERSION
          and set(tmpl) == {"schema_version", "coder_id", "packet_fingerprint_sha256", "tasks"}
          and all(set(t) == TASK_KEYS and all(set(e) == J1_KEYS for e in t["J1"])
                  for t in tmpl["tasks"].values())
          and all(len(tmpl["tasks"][tid]["J1"]) ==
                  len(key["tasks"][tid]["case_situations_source_order"])
                  for tid in key["tasks"]),
          "blank template matches the frozen validator schema and the key's case counts")
    r = subprocess.run([sys.executable, str(HERE / "validate_study1_submission.py"),
                        str(HERE / "run1_package/answers_template.json"),
                        "--package", str(HERE / "run1_package")],
                       capture_output=True, text=True)
    structural = any(s in r.stdout for s in ("keys are", "case numbers", "task(s) absent",
                                             "no counterpart", "entries,"))
    blank_only = ("not recorded as a boolean" in r.stdout and "confidence" in r.stdout)
    check(r.returncode == 1 and blank_only and not structural,
          "validator rejects the blank template for blankness only, never for structure")

    report.update({"protocol_sha256": PROTOCOL_SHA, "selection_sha256": SELECTION_SHA,
                   "seeds": seeds, "n_tasks": 90, "n_cases": n_cases,
                   "canonical_payload_sha256": payload, "checks_failed": fails})
    (HERE / "packet_audit_report.json").write_text(json.dumps(report, indent=2))
    print(f"\n{'PACKET AUDIT PASSED' if not fails else str(len(fails)) + ' FAILURE(S)'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
