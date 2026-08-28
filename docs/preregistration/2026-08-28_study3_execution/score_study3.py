"""Study 3 — final classification and the three-layer report. Frozen before any outcome.

Classification is a pure function of two frozen derivations: classify(ds, vo) → DS / VO /
UR, with DS ∧ VO a HARD STOP (instrument-defect halt; nothing is reconciled, the process
exits). Writer declarations are read only to print the §7 descriptive distribution; they
enter no classification path (classify() cannot see them).

Output, exactly the frozen protocol §7 list and nothing else:
  - counts and shares P̂(DS), P̂(VO), P̂(UR) over the m measured-eligible tasks;
  - the SAMPLE IDENTIFICATION REGION [P̂(DS), 1−P̂(VO)] — a descriptive identification
    statement, NOT a confidence interval, and never labelled as one;
  - L1: exactly two Clopper–Pearson 95% intervals conditional on the realized m (π_DS,
    π_VO). No percentile-bootstrap CI, no Imbens–Manski interval, no combined interval of
    any kind is computed anywhere in this file;
  - L2: the frozen sensitivity contrasts — DS either-run profile vs the both-runs
    definition; eligibility both-agree (m) vs either-agree count;
  - baseline eligibility rate, realized m (a result, not a target; m = 0 branch
    prespecified), writer declaration distribution, coupling-claim count, rejected VO
    claims (descriptive).

A self-guard scans the serialized output for banned inference vocabulary
("bootstrap", "imbens", "combined_interval", a bare "confidence_interval" key) and refuses
to write if any appears — the scorer cannot mislabel its own layers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scipy import stats

from study3_pins import load_frozen_sums, sha256_file

HERE = Path(__file__).resolve().parent
OUT = HERE / "results_study3.json"

BANNED_OUTPUT = ("bootstrap", "imbens", "combined_interval", '"confidence_interval"')


def cp_interval(k: int, n: int) -> list[float]:
    """Clopper–Pearson 95%, conditional on n. The audit-adopted L1 estimator."""
    if n == 0:
        return [0.0, 1.0]
    lo = 0.0 if k == 0 else float(stats.beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(0.975, k + 1, n - k))
    return [lo, hi]


def map_ds_to_baseline(ds: dict, elig: dict) -> dict:
    """The baseline (P…) and S′ (Q…) task-id namespaces meet only through the shared
    source index; mechanical re-keying, nothing else."""
    idx_to_q = {v: k for k, v in ds["task_index"].items()}
    return {"per_task": {t: ds["per_task"][idx_to_q[elig["eligible_indices"][t]]]
                         for t in elig["eligible_task_ids"]}}


def classify(ds: bool, vo: bool) -> str:
    """Pure. Sees nothing but the two frozen derivations' booleans."""
    if ds and vo:
        sys.exit("HARD STOP — DS and VO certified for the same task: instrument/procedure "
                 "defect (protocol §6). Interpretation stops here; nothing is reconciled "
                 "silently and no classification is emitted.")
    return "DS" if ds else "VO" if vo else "UR"


def score(elig: dict, ds: dict, vo: dict, writer_declarations: dict | None) -> dict:
    m = elig["m"]
    results: dict = {
        "n_drawn": elig["n_drawn"],
        "m_measured_eligible": m,
        "m_note": "m is a result, not a target (CR-1: no supplemental draw whatever m is)",
        "baseline_eligibility_rate": m / elig["n_drawn"] if elig["n_drawn"] else None,
    }
    if m == 0:
        results["no_eligible_tasks"] = True
        for layer in ("classification", "L0_sample_identification_region",
                      "L1_sampling_clopper_pearson", "L2_measurement_sensitivity"):
            results[layer] = "no eligible tasks (prespecified m = 0 branch)"
        return results

    per_task = {}
    for tid in elig["eligible_task_ids"]:
        d = ds["per_task"][tid]["ds_both_runs"]
        v = tid in vo["vo_tasks"]
        per_task[tid] = classify(d, v)
    k_ds = sum(1 for c in per_task.values() if c == "DS")
    k_vo = sum(1 for c in per_task.values() if c == "VO")
    k_ur = m - k_ds - k_vo

    results["classification"] = {"per_task": per_task,
                                 "counts": {"DS": k_ds, "VO": k_vo, "UR": k_ur},
                                 "shares": {"P_hat_DS": k_ds / m, "P_hat_VO": k_vo / m,
                                            "P_hat_UR": k_ur / m}}
    results["L0_sample_identification_region"] = {
        "region": [k_ds / m, 1 - k_vo / m],
        "statement": "descriptive identification statement over the measured-eligible "
                     "sample; NOT a confidence interval; width = P_hat_UR "
                     "(identification, irreducible by sample size)"}
    results["L1_sampling_clopper_pearson"] = {
        "pi_ds_cp95": cp_interval(k_ds, m),
        "pi_vo_cp95": cp_interval(k_vo, m),
        "conditional_on_m": m,
        "targets": "procedure-inclusive pi_DS, pi_VO over the eligible subpopulation "
                   "(frozen eligibility rule); FPC ignored (conservative); per-endpoint "
                   "only, never merged with L0 or each other"}
    results["L2_measurement_sensitivity"] = {
        "ds_either_run_share_sensitivity_only":
            sum(ds["per_task"][t]["ds_either_run_sensitivity_only"]
                for t in elig["eligible_task_ids"]) / m,
        "ds_both_runs_definition_share": k_ds / m,
        "eligibility_both_agree_m": m,
        "eligibility_either_agree_count_sensitivity_only":
            elig["either_agree_count_sensitivity_only"],
        "note": "sensitivity descriptives only; never a confirmatory classification"}
    results["descriptive"] = {
        "rejected_vo_claims": len(vo.get("rejected_claims", [])),
        "vo_classes": {c["class"]: sum(1 for x in vo["vo_tasks"].values()
                                       if x["class"] == c["class"])
                       for c in vo["vo_tasks"].values()} if vo["vo_tasks"] else {},
    }
    if writer_declarations is not None:
        dist: dict[str, int] = {}
        for t in writer_declarations["tasks"].values():
            code = (t.get("failure") or {}).get("code") or "none"
            dist[code] = dist.get(code, 0) + 1
        results["descriptive"]["writer_declaration_distribution"] = dist
        results["descriptive"]["coupling_claims_F1"] = dist.get("F1_LIST_COUPLING", 0)
        results["descriptive"]["note"] = ("writer declarations are descriptive only; they "
                                          "enter no classification path")
    return results


def main() -> None:
    if OUT.exists():
        sys.exit("results_study3.json already exists; a frozen scoring is never redone")
    elig = json.loads((HERE / "eligibility_study3.json").read_text())

    if elig["m"] == 0:
        results = score(elig, {}, {}, None)
    else:
        ds = json.loads((HERE / "ds_derivation.json").read_text())
        vo = json.loads((HERE / "vo_certificates.json").read_text())
        ds_by_baseline_tid = map_ds_to_baseline(ds, elig)
        writer = None
        wpath = HERE / "writer_handoff/study3_writer_ACCEPTED.json"
        if wpath.exists():
            frozen = load_frozen_sums(HERE / "writer_handoff/SHA256SUMS_WRITER_FROZEN")
            if sha256_file(wpath) != frozen[wpath.name]:
                sys.exit("writer output does not match its frozen hash; refusing to score")
            writer = json.loads(wpath.read_text())
        results = score(elig, ds_by_baseline_tid, vo, writer)

    serialized = json.dumps(results, indent=1, ensure_ascii=False)
    hits = [b for b in BANNED_OUTPUT if b in serialized.lower()]
    if hits:
        sys.exit(f"self-guard: banned inference vocabulary in output {hits}; refusing to write")
    OUT.write_text(serialized + "\n")
    print(serialized)
    print(f"\nresults sha256 {sha256_file(OUT)} — freeze this hash")


if __name__ == "__main__":
    main()
