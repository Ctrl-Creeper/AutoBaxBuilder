"""Study 1 — prevalence scoring and analysis. Frozen before either run starts.

Computes exactly what the frozen protocol §3–§5 prescribes, and nothing else:

  - per-run case-weighted determination rates θ_all / θ_cap / θ_saf;
  - the prespecified primary point estimate: the two-run mean, per stratum;
  - the measurement-disagreement interval per stratum:
      [rate counting only cases BOTH runs call determined,
       rate counting cases EITHER run calls determined];
  - task-cluster bootstrap (tasks resampled with replacement, cases carried along)
    for 95% CIs on all of the above; seed derived from the frozen protocol hash;
  - internal reliability on originals: raw agreement and task-cluster-aware kappa
    (per-task chance agreement, case-weighted — the Round-2 estimator, re-stated
    here self-contained), with a bootstrap CI;
  - per-run binary ICC — computed solely as the planning value the frozen protocol
    §6.1 requires for the replication arm's sample-size arithmetic;
  - the task-level "any safety case determined" rate per run, reported as the
    protocol's secondary, derived and brittle;
  - the security_policy quote-location analysis, stated as bounds: mechanical
    substring location of each quote in the labelled segments of S_t; class (a)
    locates only in security_policy, class (b) locates in at least one other
    component, and a quote locatable in S_t but in no single segment is recorded
    as a limitation and counted toward neither bound. Quotes cite and locate;
    nothing here attributes a source. Descriptive only, no threshold.

No metric outside that list is computed. Nothing is adjudicated; where the runs
disagree, both readings are carried into the interval, never resolved.

Runs only after BOTH submissions are independently frozen; verifies each against
submissions/SHA256SUMS_FROZEN before reading a single judgement.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(OUT))

from build_study1_packets import (BEGIN_S, END_S, PROTOCOL_SHA,  # noqa: E402
                                  render_segments)

RUNS = ("run1", "run2")
STRATA = ("all", "capability", "safety")
B = 2000
SEED = int(PROTOCOL_SHA[:8], 16)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


# ---------------------------------------------------------------- alignment

def align(key: dict, subs: dict[str, dict]) -> list[dict]:
    """One row per source case, both runs' judgements attached. Arithmetic only."""
    rows = []
    for tid in sorted(key["tasks"]):
        meta = key["tasks"][tid]
        situations = meta["case_situations_source_order"]
        n = len(situations)
        j1 = {r: {e["case"]: e for e in subs[r]["tasks"][tid]["J1"]} for r in RUNS}
        for r in RUNS:
            order = meta[f"{r}_case_order"]
            if sorted(order) != list(range(n)):
                sys.exit(f"{tid}: {r} case order is not a permutation")
            if sorted(j1[r]) != list(range(1, n + 1)):
                sys.exit(f"{tid}: {r} case numbers are not 1..{n}")
        for s in range(n):
            row = {"task": tid, "source_index": s, "situation": situations[s]}
            for r in RUNS:
                pos = meta[f"{r}_case_order"].index(s) + 1
                e = j1[r][pos]
                row[f"{r}_determined"] = bool(e["determined"])
                row[f"{r}_quote"] = e.get("quote") or ""
                row[f"{r}_confidence"] = e.get("confidence")
            rows.append(row)
    return rows


# ---------------------------------------------------------------- estimators

def in_stratum(row: dict, stratum: str) -> bool:
    return stratum == "all" or row["situation"] == stratum


def rates(rows: list[dict]) -> dict:
    """Every protocol §3 quantity, over the given rows. Pure function for bootstrap reuse."""
    out: dict = {}
    for st in STRATA:
        sub = [r for r in rows if in_stratum(r, st)]
        n = len(sub)
        if n == 0:
            out[st] = None
            continue
        per_run = {r: sum(x[f"{r}_determined"] for x in sub) / n for r in RUNS}
        both = sum(x["run1_determined"] and x["run2_determined"] for x in sub) / n
        either = sum(x["run1_determined"] or x["run2_determined"] for x in sub) / n
        out[st] = {"n_cases": n, "per_run": per_run,
                   "primary_two_run_mean": (per_run["run1"] + per_run["run2"]) / 2,
                   "disagreement_interval": [both, either]}
    tasks = sorted({r["task"] for r in rows})
    out["task_level_any_safety_determined"] = {
        run: sum(any(x[f"{run}_determined"] for x in rows
                     if x["task"] == t and x["situation"] == "safety")
                 for t in tasks) / len(tasks)
        for run in RUNS}
    return out


def _agree(x: np.ndarray, y: np.ndarray) -> float:
    return float((x == y).mean())


def stratified_kappa(x: np.ndarray, y: np.ndarray, g: np.ndarray) -> float:
    """Task-cluster-aware kappa: chance agreement estimated within task, then averaged."""
    po_num = pe_num = n_tot = 0.0
    for t in np.unique(g):
        m = g == t
        n = int(m.sum())
        xt, yt = x[m], y[m]
        r1, r2 = xt.mean(), yt.mean()
        po_num += _agree(xt, yt) * n
        pe_num += (r1 * r2 + (1 - r1) * (1 - r2)) * n
        n_tot += n
    po, pe = po_num / n_tot, pe_num / n_tot
    return float("nan") if pe >= 1 else (po - pe) / (1 - pe)


def icc_binary(x: np.ndarray, g: np.ndarray) -> float:
    """Between-task share of variance; protocol §6.1 planning value only."""
    rates_ = np.array([x[g == t].mean() for t in np.unique(g)])
    within = np.mean([x[g == t].var() for t in np.unique(g)])
    return float(rates_.var() / (rates_.var() + within)) if (rates_.var() + within) > 0 else 0.0


def bootstrap(rows: list[dict], b: int = B, seed: int = SEED) -> dict:
    """Task-cluster bootstrap: resample tasks with replacement, carry every case."""
    rng = np.random.default_rng(seed)
    by_task: dict[str, list[dict]] = {}
    for r in rows:
        by_task.setdefault(r["task"], []).append(r)
    tasks = sorted(by_task)
    stats: dict[str, list[float]] = {}

    def record(name: str, v: float) -> None:
        stats.setdefault(name, []).append(v)

    for _ in range(b):
        drawn = rng.choice(tasks, size=len(tasks), replace=True)
        # tasks must stay distinct clusters after resampling, so re-label each draw
        sample = [dict(row, task=f"{t}#{i}") for i, t in enumerate(drawn) for row in by_task[t]]
        rt = rates(sample)
        for st in STRATA:
            if rt[st] is None:
                continue
            for run in RUNS:
                record(f"theta_{st}_{run}", rt[st]["per_run"][run])
            record(f"theta_{st}_mean", rt[st]["primary_two_run_mean"])
            record(f"interval_{st}_both", rt[st]["disagreement_interval"][0])
            record(f"interval_{st}_either", rt[st]["disagreement_interval"][1])
        x = np.array([r["run1_determined"] for r in sample], dtype=float)
        y = np.array([r["run2_determined"] for r in sample], dtype=float)
        g = np.array([r["task"] for r in sample])
        k = stratified_kappa(x, y, g)
        if np.isfinite(k):
            record("kappa_cluster", k)

    return {name: {"ci95": [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))],
                   "replicates": len(v)}
            for name, v in stats.items()}


# ------------------------------------------------- security_policy bounds

def locate(quote: str, segments: dict[str, str]) -> list[str]:
    q = norm(quote)
    return [name for name, text in segments.items() if q and q in norm(text)]


def policy_bounds(rows: list[dict], segments_by_task: dict[str, dict[str, str]]) -> dict:
    out: dict = {"note": ("mechanical quote location only; quotes cite and locate, nothing here "
                          "attributes a source; descriptive, no threshold")}
    per_case_class: dict[str, dict] = {}
    for run in RUNS:
        det = [r for r in rows if r["situation"] == "safety" and r[f"{run}_determined"]]
        counts = {"policy_only": 0, "other_field": 0, "spans_components": 0}
        for r in det:
            comps = locate(r[f"{run}_quote"], segments_by_task[r["task"]])
            cls = ("other_field" if any(c != "security_policy" for c in comps)
                   else "policy_only" if comps == ["security_policy"]
                   else "spans_components")
            counts[cls] += 1
            per_case_class.setdefault(f"{r['task']}/{r['source_index']}", {})[run] = cls
        n = len(det)
        entry = {"determined_safety_cases": n, "counts": counts}
        if n:
            b_rate = counts["other_field"] / n
            entry["survival_lower_bound"] = b_rate
            if counts["spans_components"] == 0:
                entry["switch_removable_at_most"] = counts["policy_only"] / n
            else:
                entry["switch_removable_at_most"] = 1 - b_rate
                entry["limitation"] = (f"{counts['spans_components']} quote(s) locate in S_t but "
                                       "in no single segment; the at-most figure falls back to "
                                       "1 - survival_lower_bound, per the frozen mechanical-rule "
                                       "limitation discipline")
        out[run] = entry

    both = [r for r in rows if r["situation"] == "safety"
            and r["run1_determined"] and r["run2_determined"]]
    agree_counts = {"both_other_field": 0, "both_policy_only": 0, "mixed_or_spanning": 0}
    for r in both:
        cls = per_case_class.get(f"{r['task']}/{r['source_index']}", {})
        pair = (cls.get("run1"), cls.get("run2"))
        if pair == ("other_field", "other_field"):
            agree_counts["both_other_field"] += 1
        elif pair == ("policy_only", "policy_only"):
            agree_counts["both_policy_only"] += 1
        else:
            agree_counts["mixed_or_spanning"] += 1
    out["both_agree_variant"] = {"cases_both_runs_determined": len(both), **agree_counts}
    if both:
        out["both_agree_variant"]["survival_lower_bound"] = \
            agree_counts["both_other_field"] / len(both)
    return out


# ---------------------------------------------------------------- main

def main() -> None:
    key = json.loads((OUT / "sealed/_KEY_DO_NOT_SHOW_CODERS.json").read_text())
    frozen = dict(line.split()[::-1] for line in
                  (OUT / "submissions/SHA256SUMS_FROZEN").read_text().strip().splitlines())
    subs = {}
    for run in RUNS:
        p = OUT / f"submissions/{run}_answers_FROZEN.json"
        if hashlib.sha256(p.read_bytes()).hexdigest() != frozen[p.name]:
            sys.exit(f"{p.name} does not match its frozen hash; refusing to score")
        subs[run] = json.loads(p.read_text())

    rows = align(key, subs)

    from secodeplt_task_runner import load  # noqa: E402  (benchmark loader only)
    records = {r["index"]: r for r in load(only_stdlib=False)}
    segments_by_task = {}
    for tid, meta in key["tasks"].items():
        seg = render_segments(records[meta["index"]])
        packet = (OUT / f"run1_package/tasks/{tid}.md").read_text()
        shown = packet.split(BEGIN_S, 1)[1].split(END_S, 1)[0].strip()
        for name, text in seg.items():
            if norm(text) not in norm(shown):
                sys.exit(f"{tid}: segment {name} not found in the S presented; refusing to score")
        segments_by_task[tid] = seg

    x = np.array([r["run1_determined"] for r in rows], dtype=float)
    y = np.array([r["run2_determined"] for r in rows], dtype=float)
    g = np.array([r["task"] for r in rows])

    results = {
        "protocol_sha256": PROTOCOL_SHA,
        "submission_sha256": frozen,
        "n_tasks": len(key["tasks"]), "n_cases": len(rows),
        "estimates": rates(rows),
        "reliability_internal": {
            "raw_agreement": _agree(x, y),
            "kappa_cluster_aware": stratified_kappa(x, y, g),
            "note": ("independent blinded coding runs, not independent human coders; "
                     "Round-2 kappa is transport evidence only, this figure is Study 1's own")},
        "icc_planning_value_per_run": {"run1": icc_binary(x, g), "run2": icc_binary(y, g),
                                       "purpose": "replication-arm sample-size arithmetic only"},
        "bootstrap": {"B": B, "seed": SEED,
                      "seed_derivation": "int(study1_protocol_sha256[:8], 16)",
                      "ci": bootstrap(rows)},
        "security_policy_bounds": policy_bounds(rows, segments_by_task),
        "alignment_rows": rows,
    }
    (OUT / "results_study1_prevalence.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False))

    show = {k: v for k, v in results.items() if k != "alignment_rows"}
    print(json.dumps(show, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
