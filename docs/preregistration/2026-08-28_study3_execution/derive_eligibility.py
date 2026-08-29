"""Study 3 — mechanical derivation of measured eligibility from the frozen baseline runs.

Runs ONLY after both baseline submissions are independently frozen (verified against
submissions_baseline/SHA256SUMS_BASELINE_FROZEN before a single judgement is read). Opens
the baseline sealed key solely to align cases and read the sealed situation labels; nothing
is adjudicated, and no human decision enters anywhere in this file.

The frozen rule (protocol §3, verbatim): a task is measured-eligible iff at least one
safety case is determined in BOTH runs — read at case level (there exists a safety case
both runs call determined; "both-agree", the measurement-conservative rule). The either-
agree variant (some safety case determined in at least one run) is computed here only as
the L2 sensitivity input; it never gates anything.

m is a result, never a target. If m = 0, the manifest still freezes, every downstream
stage reports "no eligible tasks", and nothing is drawn again — prespecified, per CR-1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from study3_pins import RUNS, align_runs, load_frozen_sums, sha256_file

HERE = Path(__file__).resolve().parent
SUBS = HERE / "submissions_baseline"
OUT = HERE / "eligibility_study3.json"


def eligibility(rows: list[dict]) -> dict:
    per_task: dict[str, dict] = {}
    for tid in sorted({r["task"] for r in rows}):
        t = [r for r in rows if r["task"] == tid]
        saf = [r for r in t if r["situation"] == "safety"]
        qualifying = [r["source_index"] for r in saf
                      if r["run1_determined"] and r["run2_determined"]]
        either = sum(r["run1_determined"] or r["run2_determined"] for r in saf)
        per_task[tid] = {
            "n_capability": sum(r["situation"] == "capability" for r in t),
            "n_safety": len(saf),
            "safety_determined_both": len(qualifying),
            # the mechanical case IDs (source-order indices) that make the rule hold;
            # quotes are deliberately NOT copied into this manifest
            "qualifying_safety_case_source_indices": qualifying,
            "safety_determined_either": either,
            "eligible_both_agree": len(qualifying) >= 1,
            "eligible_either_agree_sensitivity_only": either >= 1,
        }
    return per_task


def main() -> None:
    if OUT.exists():
        sys.exit("eligibility_study3.json already exists; a frozen derivation is never redone")
    frozen = load_frozen_sums(SUBS / "SHA256SUMS_BASELINE_FROZEN")
    subs = {}
    for run in RUNS:
        p = SUBS / f"{run}_baseline_FROZEN.json"
        if sha256_file(p) != frozen[p.name]:
            sys.exit(f"{p.name} does not match its frozen hash; refusing to derive")
        subs[run] = json.loads(p.read_text())

    key = json.loads((HERE / "baseline/sealed/_KEY_DO_NOT_SHOW_CODERS.json").read_text())
    rows = align_runs(key, subs)
    per_task = eligibility(rows)

    eligible = sorted(t for t, v in per_task.items() if v["eligible_both_agree"])
    manifest = {
        "rule": "measured-eligible iff >=1 safety case determined in both runs "
                "(case-level both-agree; frozen a priori, protocol §3)",
        "m": len(eligible),
        "eligible_task_ids": eligible,
        "eligible_indices": {t: key["tasks"][t]["index"] for t in eligible},
        "either_agree_count_sensitivity_only":
            sum(v["eligible_either_agree_sensitivity_only"] for v in per_task.values()),
        "n_drawn": len(per_task),
        "per_task": per_task,
        "baseline_submission_sha256": frozen,
    }
    OUT.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(f"measured eligibility derived mechanically: m = {manifest['m']} of "
          f"{manifest['n_drawn']} drawn (a result, not a target)")
    if manifest["m"] == 0:
        print("m = 0: prespecified branch — every layer reports 'no eligible tasks'; "
              "no supplemental draw exists under CR-1")
    print(f"eligibility manifest sha256 {sha256_file(OUT)} — freeze this hash")


if __name__ == "__main__":
    main()
