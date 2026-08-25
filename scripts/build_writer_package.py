"""Build the specification-writer handoff package for the frozen Round-2 selection.

The writer's blind boundary is set by the writer's own task, not by minimising what
they know. Both case lists are shown **with their labels**, because the rewrite is
defined relative to them: keep List A settled, leave List B open. Withholding the
labels would not blind the writer, it would make the task impossible. The coders,
whose task is different, receive the same cases merged and unlabelled.

Withheld because none of it bears on the rewrite: any coder judgement, the earlier
development round and its provenance, the classification vocabulary, expected
proportions, and the CWE identifier.

Every variable byte in a task file comes from the selected record. The contamination
check regenerates each file from source and compares, so the package is verified by
provenance rather than by scanning it for words — lexical absence has already been
shown, in this project, not to imply informational absence.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from secodeplt_task_runner import load  # noqa: E402

SEL = Path("docs/preregistration/2026-08-25_round2_selection/round2_selection.json")
OUT = Path("docs/preregistration/2026-08-25_writer_handoff")
PKG = OUT / "writer_package"

_DUMP = ('\nimport json\nprint("###" + json.dumps([{"situation": s, "input": repr(k), '
         '"expected": getattr(e, "__name__", None) or repr(e)} for s, cs in testcases.items() '
         'for k, e in cs]))\n')
PROSE = ("description", "context", "arguments", "return", "raise", "security_policy")


def extract_cases(rec: dict) -> list[dict]:
    with tempfile.TemporaryDirectory() as t:
        f = Path(t) / "c.py"
        f.write_text(rec["unittest"]["setup"] + "\n" + rec["unittest"]["testcases"] + _DUMP)
        out = subprocess.run([sys.executable, str(f)], cwd=t, capture_output=True,
                             text=True, timeout=60).stdout
    return json.loads(out.split("###", 1)[1])


def signature(rec: dict) -> str:
    for line in rec["ground_truth"]["code_before"].splitlines():
        if re.match(r"\s*def\s", line):
            return line.strip()
    return "(signature not found)"


def render(wid: str, rec: dict, cases: list[dict]) -> str:
    td = rec["task_description"]
    a = [c for c in cases if c["situation"] == "capability"]
    b = [c for c in cases if c["situation"] == "safety"]
    L = [f"# Task {wid}", "",
         "## Original specification", "",
         f"**Function name:** `{td['function_name']}`",
         f"**Signature:** `{signature(rec)}`", ""]
    for f in PROSE:
        label = "Security Policy" if f == "security_policy" else f.capitalize()
        L += [f"**{label}:** {td.get(f) or 'None'}", ""]
    L += ["## Setup / preamble code (frozen — copied for you, do not retype)", "",
          "```python", rec["unittest"]["setup"].strip() or "(none)", "```", "",
          "## List A — your candidate must settle every one of these", "",
          "| # | input | expected behaviour |", "|---|---|---|"]
    L += [f"| A{i} | `{c['input']}` | `{c['expected']}` |" for i, c in enumerate(a, 1)]
    L += ["", "## List B — your candidate must leave every one of these unsettled", "",
          "| # | input | expected behaviour |", "|---|---|---|"]
    L += [f"| B{i} | `{c['input']}` | `{c['expected']}` |" for i, c in enumerate(b, 1)]
    L += ["", "## Reminder", "",
          "Rewrite the five prose fields only. The signature, the setup code and every case are",
          "frozen. Produce a candidate for this task whether or not both conditions can be met; if",
          "they cannot, record a failure code from the taxonomy in INSTRUCTIONS.md §4.", ""]
    return "\n".join(L)


def main() -> None:
    (PKG / "tasks").mkdir(parents=True, exist_ok=True)
    (OUT / "sealed").mkdir(exist_ok=True)
    (OUT / "validation").mkdir(exist_ok=True)

    man = json.loads(SEL.read_text())
    selection, protocol = man["selection"], man["protocol"]
    records = {r["index"]: r for r in load(only_stdlib=False)}

    # Presentation order is derived from the protocol hash, as the selection was;
    # it carries no information and is recorded so the mapping is reconstructible.
    order = np.random.default_rng(int(protocol[8:16], 16)).permutation(len(selection))
    key, tmpl = {}, {}

    for pos, i in enumerate(order, 1):
        idx = selection[int(i)]
        wid = f"W{pos:02d}"
        rec = records[idx]
        cases = extract_cases(rec)
        (PKG / "tasks" / f"{wid}.md").write_text(render(wid, rec, cases))
        key[wid] = {"index": idx,
                    "case_order": [{"list": "A" if c["situation"] == "capability" else "B",
                                    "situation": c["situation"]} for c in cases]}
        tmpl[wid] = {
            "spec": {f: "" for f in PROSE if f != "security_policy"},
            "edits": [], "sufficiency_evidence": [], "failure": None, "notes": "",
        }

    (PKG / "output_template.json").write_text(
        json.dumps({"writer_id": "", "tasks": tmpl}, indent=2))
    (OUT / "sealed" / "_KEY_DO_NOT_SHOW_WRITER.json").write_text(
        json.dumps({"order_seed_derivation": f"int(protocol_sha256[8:16], 16) = {int(protocol[8:16], 16)}",
                    "protocol": protocol, "mapping": key}, indent=2))

    files = {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(PKG.rglob("*")) if p.is_file()}
    roll = hashlib.sha256("".join(f"{k}:{v}\n" for k, v in sorted(files.items())).encode()).hexdigest()
    (OUT / "writer_package_manifest.json").write_text(
        json.dumps({"protocol": protocol, "selection_sha256":
                    hashlib.sha256(SEL.read_bytes()).hexdigest(),
                    "files": files, "package_sha256": roll}, indent=2))

    print(f"tasks written  {len(key)}")
    print(f"package files  {len(files)}")
    print(f"package_sha256 {roll}")


if __name__ == "__main__":
    main()
