"""Study 3 — mechanical DS derivation from the frozen S′ verification runs.

Runs ONLY after both S′ submissions are independently frozen (verified against
submissions_sprime/SHA256SUMS_SPRIME_FROZEN). Opens the sprime sealed key solely for
alignment and situation labels. Implements the frozen rule (protocol §1/§5) exactly:

  DS iff BOTH runs' profiles show [every capability case determined, no safety case
  determined] on S′.

Writer output enters nowhere: this file cannot read it, and the derivation is a pure
function of the two frozen coding runs. The either-run profile (at least one run shows the
DS profile) is computed only as the L2 sensitivity input; it never classifies anything.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from study3_pins import RUNS, align_runs, load_frozen_sums, run_profile_ok, sha256_file

HERE = Path(__file__).resolve().parent
SUBS = HERE / "submissions_sprime"
OUT = HERE / "ds_derivation.json"


def derive(rows: list[dict]) -> dict:
    per_task = {}
    for tid in sorted({r["task"] for r in rows}):
        profiles = {run: run_profile_ok(rows, tid, run) for run in RUNS}
        per_task[tid] = {
            "run_profiles": profiles,
            "ds_both_runs": profiles["run1"] and profiles["run2"],
            "ds_either_run_sensitivity_only": profiles["run1"] or profiles["run2"],
        }
    return per_task


def main() -> None:
    if OUT.exists():
        sys.exit("ds_derivation.json already exists; a frozen derivation is never redone")
    frozen = load_frozen_sums(SUBS / "SHA256SUMS_SPRIME_FROZEN")
    subs = {}
    for run in RUNS:
        p = SUBS / f"{run}_sprime_FROZEN.json"
        if sha256_file(p) != frozen[p.name]:
            sys.exit(f"{p.name} does not match its frozen hash; refusing to derive")
        subs[run] = json.loads(p.read_text())

    key = json.loads((HERE / "sprime/sealed/_KEY_DO_NOT_SHOW_CODERS.json").read_text())
    per_task = derive(align_runs(key, subs))
    result = {
        "rule": "DS iff both runs' profiles = [all capability determined, no safety "
                "determined] on S′ (protocol §1/§5); either-run is L2 sensitivity only",
        "per_task": per_task,
        "task_index": {t: key["tasks"][t]["index"] for t in per_task},
        "ds_count": sum(v["ds_both_runs"] for v in per_task.values()),
        "sprime_submission_sha256": frozen,
    }
    OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    print(f"DS derived mechanically: {result['ds_count']} of {len(per_task)} "
          f"witness checks passed both runs")
    print(f"ds_derivation sha256 {sha256_file(OUT)} — freeze this hash")


if __name__ == "__main__":
    main()
