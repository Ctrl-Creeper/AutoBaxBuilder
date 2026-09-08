#!/usr/bin/env python3
"""Build the blinded coding packet for the Study-4B mechanism disambiguation.

POST-HOC EXPLORATORY. Read-only over frozen Study-4B artifacts. Runs the frozen
CAPABILITY test cases only (never the safety cases) to collect the minimal
diagnostic the frozen rubric allows. Writes a blinded packet plus a sealed key.
"""

from __future__ import annotations

import hashlib
import json
import random
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXEC_DIR = HERE.parent.parent / "preregistration/2026-09-08_study4b_execution"
sys.path.insert(0, str(EXEC_DIR))
import study4b_execute as ex  # noqa: E402

RUBRIC = HERE / "RUBRIC_FROZEN.md"
SAMPLE_SIZE = 20

# capability-only diagnostic harness: records status AND observed behaviour
_DIAG = r"""
import json, os, signal, traceback

class TimeoutException(Exception):
    pass

def _timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, _timeout_handler)
out = []
for case in testcases["capability"]:
    entry = {}
    expected = case[1]
    try:
        signal.alarm(10)
        if isinstance(expected, type) and issubclass(expected, Exception):
            try:
                __func(**case[0])
                entry = {"status": "no_raise", "observed": "returned normally"}
            except expected:
                entry = {"status": "pass", "observed": "raised as required"}
        else:
            got = __func(**case[0])
            same = str(got) == str(expected)
            entry = {"status": "pass" if same else "wrong_value",
                     "observed": repr(got)[:400]}
        signal.alarm(0)
    except TimeoutException:
        entry = {"status": "timeout", "observed": "exceeded 10s"}
    except Exception as exc:
        signal.alarm(0)
        entry = {"status": "raised",
                 "observed": type(exc).__name__ + ": " + str(exc)[:300]}
    out.append(entry)
with open(os.environ["DIAG_PATH"], "w") as f:
    json.dump(out, f)
"""


def run_diagnostic(execution: dict, code: str) -> list[dict] | str:
    program = "\n".join([
        execution["setup"], code, execution["testcases"],
        f"__func = {execution['function_name']}", _DIAG,
    ])
    with tempfile.TemporaryDirectory(prefix="s4b-diag-") as tmp:
        d = Path(tmp)
        (d / "p.py").write_text(program)
        try:
            proc = subprocess.run(
                [sys.executable, str(d / "p.py")], cwd=d, capture_output=True,
                text=True, timeout=120,
                env={"DIAG_PATH": str(d / "r.json"), "PATH": "/usr/bin:/bin"},
            )
        except subprocess.TimeoutExpired:
            return "PROGRAM_TIMEOUT"
        if not (d / "r.json").exists():
            tail = (proc.stderr or "").strip().splitlines()
            return "DID_NOT_RUN: " + (tail[-1] if tail else "no output")
        return json.loads((d / "r.json").read_text())


def main() -> None:
    rubric_sha = hashlib.sha256(RUBRIC.read_bytes()).hexdigest()
    stim = ex.load_json(ex.STIMULI)
    ev = ex.load_json(ex.EVALUATION)
    stim_sha = ex.sha256_file(ex.STIMULI)
    ev_sha = ex.sha256_file(ex.EVALUATION)

    seed = int.from_bytes(
        hashlib.sha256(f"{stim_sha}|{ev_sha}|{rubric_sha}".encode()).digest()[:8],
        "big",
    )
    rng = random.Random(seed)

    rows = defaultdict(dict)
    for r in ev["rows"]:
        rows[r["ds_task_id"]][(r["condition"], r["repeat"])] = r

    frame = sorted(
        t for t, rs in rows.items()
        if sum(v["capability_pass"] for k, v in rs.items() if k[0] == "S")
        < sum(v["capability_pass"] for k, v in rs.items() if k[0] == "Sprime")
    )
    sample = sorted(rng.sample(frame, SAMPLE_SIZE))

    pairs = {p["ds_task_id"]: p for p in stim["pairs"]}
    packet, key = [], []
    for task in sample:
        rs = rows[task]
        s_fail = sorted(k[1] for k, v in rs.items()
                        if k[0] == "S" and not v["capability_pass"])
        sp_pass = sorted(k[1] for k, v in rs.items()
                         if k[0] == "Sprime" and v["capability_pass"])
        flag = not (s_fail and sp_pass)
        s_rep = rng.choice(s_fail or sorted(k[1] for k in rs if k[0] == "S"))
        sp_rep = rng.choice(sp_pass or sorted(k[1] for k in rs if k[0] == "Sprime"))
        s_row, sp_row = rs[("S", s_rep)], rs[("Sprime", sp_rep)]

        a_is_s = rng.random() < 0.5
        arms = {}
        for label, row in (("S", s_row), ("Sprime", sp_row)):
            code = ex.extract_code(ex.response_content(row["request_id"]))
            arms[label] = {
                "code": code,
                "diag": run_diagnostic(pairs[task]["execution"], code),
                "runner_status": row["runner_status"],
                "request_id": row["request_id"],
                "repeat": row["repeat"],
            }
        shown = [("A", "S" if a_is_s else "Sprime"), ("B", "Sprime" if a_is_s else "S")]

        exe = pairs[task]["execution"]
        cap_cases = [c for c in pairs[task]["oracle_cases"] if c["situation"] == "capability"]
        packet.append({
            "packet_id": f"T{len(packet) + 1:02d}",
            "function_name": exe["function_name"],
            "setup": exe["setup"],
            "capability_cases": cap_cases,
            "fallback_selection": flag,
            "arms": [
                {"label": lab, "code": arms[a]["code"], "diagnostic": arms[a]["diag"],
                 "runner_status": arms[a]["runner_status"]}
                for lab, a in shown
            ],
        })
        key.append({
            "packet_id": f"T{len(packet):02d}", "ds_task_id": task,
            "A": shown[0][1], "B": shown[1][1],
            "S_request_id": s_row["request_id"], "Sprime_request_id": sp_row["request_id"],
            "S_repeat": s_rep, "Sprime_repeat": sp_rep,
            "fallback_selection": flag,
        })

    (HERE / "CODING_KEY_SEALED.json").write_text(json.dumps(
        {"seed": seed, "rubric_sha256": rubric_sha, "stimuli_sha256": stim_sha,
         "evaluation_sha256": ev_sha, "frame_size": len(frame),
         "sample_size": SAMPLE_SIZE, "key": key}, indent=1, sort_keys=True))

    lines = ["# Blinded coding packet — Study-4B mechanism disambiguation", "",
             "Coder input only. Conditions anonymised. Capability cases only; no",
             "security information appears in this file.", ""]
    for p in packet:
        lines += [f"## {p['packet_id']} — target function `{p['function_name']}`", "",
                  "### Capability specification (frozen capability test cases)", "",
                  "Setup code available to the implementation:", "",
                  "```python", p["setup"].strip(), "```", "",
                  "Required behaviour:", ""]
        for c in p["capability_cases"]:
            lines.append(f"- `{c['input']}` → `{c['expected']}`")
        if p["fallback_selection"]:
            lines += ["", "_(selection fallback applied for one arm)_"]
        for arm in p["arms"]:
            lines += ["", f"### Implementation {arm['label']}"
                          f"  (runner: {arm['runner_status']})", "",
                      "```python", arm["code"].strip() or "<empty>", "```", "",
                      f"Capability diagnostic for {arm['label']}:", ""]
            d = arm["diagnostic"]
            if isinstance(d, str):
                lines.append(f"- did not execute: `{d}`")
            else:
                for i, e in enumerate(d):
                    lines.append(f"- case {i + 1}: **{e['status']}** — {e['observed']}")
        lines += ["", "---", ""]
    (HERE / "CODING_PACKET_BLINDED.md").write_text("\n".join(lines))
    print(f"seed={seed} frame={len(frame)} sampled={len(sample)}")


if __name__ == "__main__":
    main()
