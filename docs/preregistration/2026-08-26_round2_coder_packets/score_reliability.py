"""Steps 2-5 — the frozen C9 metric set, computed as one block.

Written and self-tested before any real value was looked at. Every metric in C9 is
computed on every run; none is selected afterwards.

Two implementation choices the protocol leaves open, fixed here rather than later:

**Task-cluster-aware kappa.** C8 permits a task-stratified estimator or a task
random effect. This uses the stratified form: expected agreement is computed inside
each task from that task's own marginals and then averaged over tasks weighted by
cases, instead of from pooled marginals. That is precisely the term the sensitivity
analysis found inflated under heterogeneity, since chance agreement is convex in the
marginal rate and pooling it understates the average. The self-test measures what
this estimator does to a known truth, including the small-task bias it introduces in
the other direction, so its behaviour is on the record before it met the data.

**Cluster bootstrap.** Tasks are resampled with replacement and every case of a
sampled task travels with it. Case-level resampling would break exactly the
within-task correlation the estimator exists to respect.

Quote concordance is exact after whitespace and case normalisation. The frozen
protocol asks whether both runs cite the same sentence but defines no algorithm, so
no similarity threshold is invented here; cases that cannot be compared mechanically
are counted separately and left to disagreement analysis.

Usage:
    score_reliability.py --self-test
    score_reliability.py --run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
ALIGN = OUT / "alignment.json"
SUBS = {"coder1": OUT / "submissions/coder1_answers_FROZEN.json",
        "coder2": OUT / "submissions/coder2_answers_FROZEN.json"}
B = 2000
# Seed derived from the two frozen submission hashes, so it could not be chosen.
SEED = int("35916e1c", 16) ^ int("1f254579", 16)


# --------------------------------------------------------------------------- metrics
def _agree(x, y):
    return float(np.mean(x == y))


def pooled_kappa(x: np.ndarray, y: np.ndarray) -> float:
    """Cohen's kappa from pooled marginals. Descriptive only, per C8."""
    po = _agree(x, y)
    r1, r2 = x.mean(), y.mean()
    pe = r1 * r2 + (1 - r1) * (1 - r2)
    return float("nan") if pe >= 1 else (po - pe) / (1 - pe)


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


def gwet_ac1(x: np.ndarray, y: np.ndarray) -> float:
    po = _agree(x, y)
    pi = (x.mean() + y.mean()) / 2
    pe = 2 * pi * (1 - pi)
    return float("nan") if pe >= 1 else (po - pe) / (1 - pe)


def icc_binary(x: np.ndarray, g: np.ndarray) -> float:
    """Share of variance in the determination indicator sitting between tasks."""
    rates = np.array([x[g == t].mean() for t in np.unique(g)])
    within = np.mean([x[g == t].var() for t in np.unique(g)])
    return float(rates.var() / (rates.var() + within)) if (rates.var() + within) > 0 else 0.0


def cluster_bootstrap(fn, x, y, g, b=B, seed=SEED):
    """Resample tasks with replacement; every case of a drawn task comes with it."""
    rng = np.random.default_rng(seed)
    tasks = np.unique(g)
    idx_by_task = {t: np.flatnonzero(g == t) for t in tasks}
    out = []
    for _ in range(b):
        drawn = rng.choice(tasks, size=len(tasks), replace=True)
        idx = np.concatenate([idx_by_task[t] for t in drawn])
        gg = np.concatenate([np.full(len(idx_by_task[t]), i) for i, t in enumerate(drawn)])
        v = fn(x[idx], y[idx], gg) if fn.__code__.co_argcount == 3 else fn(x[idx], y[idx])
        if np.isfinite(v):
            out.append(v)
    a = np.array(out)
    return (float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5)), len(a))


# --------------------------------------------------------------------------- self-test
def _synth(n_tasks, sizes, p, kappa, tau, seed):
    rng = np.random.default_rng(seed)
    xs, ys, gs = [], [], []
    for t in range(n_tasks):
        m = sizes[t % len(sizes)]
        pt = 1 / (1 + np.exp(-(np.log(p / (1 - p)) + tau * rng.standard_normal())))
        base = rng.random(m) < pt
        other = rng.random(m) < pt
        agree = rng.random(m) < kappa
        xs.append(base)
        ys.append(np.where(agree, base, other))
        gs.append(np.full(m, t))
    return np.concatenate(xs).astype(int), np.concatenate(ys).astype(int), np.concatenate(gs)


def self_test() -> None:
    ok = True

    def say(good, msg):
        nonlocal ok
        print(f"  {'ok  ' if good else 'FAIL'} {msg}")
        ok &= good

    g = np.repeat(np.arange(10), 4)
    x = np.array([1, 0] * 20)
    say(pooled_kappa(x, x) == 1.0 and stratified_kappa(x, x, g) == 1.0 and gwet_ac1(x, x) == 1.0,
        "perfect agreement gives kappa = AC1 = 1")
    say(abs(pooled_kappa(x, 1 - x) + 1.0) < 1e-9,
        f"complete disagreement on balanced marginals gives kappa = -1 ({pooled_kappa(x, 1 - x):.3f})")

    xs = np.array([1] * 38 + [0] * 2)
    ys = np.array([1] * 36 + [0] * 2 + [1] * 2)
    say(gwet_ac1(xs, ys) > pooled_kappa(xs, ys),
        f"under skewed marginals AC1 exceeds kappa ({gwet_ac1(xs, ys):.3f} vs {pooled_kappa(xs, ys):.3f})"
        " — the paradox the sensitivity is there to expose")

    sizes = [2, 3, 4, 5, 6, 9]
    x1, y1, g1 = _synth(90, sizes, 0.5, 0.7, 0.0, 1)
    x2, y2, g2 = _synth(90, sizes, 0.5, 0.7, 1.5, 2)
    pk0, sk0 = pooled_kappa(x1, y1), stratified_kappa(x1, y1, g1)
    pk1, sk1 = pooled_kappa(x2, y2), stratified_kappa(x2, y2, g2)
    say(abs(pk0 - 0.7) < 0.12, f"no clustering: pooled kappa recovers 0.70 ({pk0:.3f})")
    say(pk1 > pk0, f"with clustering pooled kappa inflates ({pk1:.3f} vs {pk0:.3f}) as the DGP predicted")
    say(sk1 < pk1, f"the stratified estimator removes that inflation ({sk1:.3f} < {pk1:.3f})")
    print(f"  note stratified estimator on unclustered data: {sk0:.3f} against a true 0.70 — "
          "per-task chance agreement is plugged in from very few cases, which biases it downward; "
          "recorded here so the real figure is read with it in view")

    say(len({len(x1[g1 == t]) for t in np.unique(g1)}) > 1, "synthetic tasks have unequal sizes")

    # the bootstrap must move whole tasks
    rng = np.random.default_rng(0)
    tasks = np.unique(g1)
    idx_by_task = {t: np.flatnonzero(g1 == t) for t in tasks}
    drawn = rng.choice(tasks, size=len(tasks), replace=True)
    idx = np.concatenate([idx_by_task[t] for t in drawn])
    say(len(idx) == sum(len(idx_by_task[t]) for t in drawn) and
        all(set(idx_by_task[t]).issubset(set(idx)) for t in set(drawn)),
        "cluster bootstrap carries every case of each drawn task")
    lo, hi, n = cluster_bootstrap(stratified_kappa, x1, y1, g1, b=300, seed=7)
    say(lo < sk0 < hi and n > 250, f"bootstrap CI brackets the point estimate ([{lo:.3f}, {hi:.3f}])")

    print(f"\n{'SELF-TEST PASSED' if ok else 'SELF-TEST FAILED'}")
    sys.exit(0 if ok else 1)


# --------------------------------------------------------------------------- run
def norm_q(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


CLASS_TABLE = [
    (True, False, True, "SEPARABLE"),
    (True, False, False, "STRUCTURALLY_CARRIED"),
    (True, True, None, "NOT_YET_BLINDED"),
    (False, None, False, "INSEPARABLE"),
    (False, None, True, "OVER_STRIPPED"),
]


def derive_class(all_cap_det: bool, any_saf_det: bool, j3_exists: bool) -> str:
    for a, b, c, name in CLASS_TABLE:
        if a == all_cap_det and (b is None or b == any_saf_det) and (c is None or c == j3_exists):
            return name
    return "UNRESOLVED"


def run() -> None:
    align = json.loads(ALIGN.read_text())
    rows = align["rows"]
    sub = {c: json.loads(p.read_text()) for c, p in SUBS.items()}

    tids = sorted({r["task"] for r in rows})
    tindex = {t: i for i, t in enumerate(tids)}
    x = np.array([int(r["coder1_determined"]) for r in rows])
    y = np.array([int(r["coder2_determined"]) for r in rows])
    g = np.array([tindex[r["task"]] for r in rows])

    res = {"n_tasks": len(tids), "n_cases": len(rows),
           "bootstrap": {"replicates": B, "seed": SEED,
                         "seed_derivation": "int(coder1_sha[:8],16) XOR int(coder2_sha[:8],16)",
                         "unit": "task, with replacement; all cases of a drawn task retained"},
           "warnings": []}

    res["raw_agreement"] = _agree(x, y)
    res["pooled_kappa_descriptive_only"] = pooled_kappa(x, y)
    res["cluster_aware_kappa_primary"] = stratified_kappa(x, y, g)
    lo, hi, n = cluster_bootstrap(stratified_kappa, x, y, g)
    res["cluster_aware_kappa_ci95"] = [lo, hi]
    if n < B:
        res["warnings"].append(f"cluster-aware kappa: {B - n} bootstrap replicates were undefined")
    res["gwet_ac1_sensitivity"] = gwet_ac1(x, y)
    lo, hi, n = cluster_bootstrap(gwet_ac1, x, y, g)
    res["gwet_ac1_ci95"] = [lo, hi]
    res["ac1_interpretation_note"] = ("AC1 is reported as a number with its interval. Cohen kappa's "
                                      "verbal scales were not built for it and are not applied.")
    if n < B:
        res["warnings"].append(f"AC1: {B - n} bootstrap replicates were undefined")

    res["marginals"] = {"coder1_determined_rate": float(x.mean()),
                        "coder2_determined_rate": float(y.mean())}
    res["icc"] = {"coder1": icc_binary(x, g), "coder2": icc_binary(y, g)}
    rates1 = np.array([x[g == i].mean() for i in range(len(tids))])
    res["between_task_variance"] = {"coder1": float(rates1.var()),
                                    "coder2": float(np.array([y[g == i].mean()
                                                              for i in range(len(tids))]).var())}

    # quote concordance — exact after normalisation, no similarity threshold
    both = [r for r in rows if r["coder1_determined"] and r["coder2_determined"]]
    exact = sum(1 for r in both if norm_q(r["coder1_quote"]) == norm_q(r["coder2_quote"]))
    uncomparable = sum(1 for r in both if not norm_q(r["coder1_quote"]) or not norm_q(r["coder2_quote"]))
    res["quote_concordance"] = {"cases_both_determined": len(both), "exact_normalised_match": exact,
                                "not_mechanically_comparable": uncomparable,
                                "rate": (exact / len(both)) if both else None,
                                "definition": "exact match after whitespace collapse and lowercasing; "
                                              "no similarity threshold was invented"}

    res["tie_break_rate"] = {c: {"tie_break": sum(1 for r in rows if r[f"{c}_confidence"] == "tie_break"),
                                 "clear": sum(1 for r in rows if r[f"{c}_confidence"] == "clear"),
                                 "rate": sum(1 for r in rows if r[f"{c}_confidence"] == "tie_break") / len(rows)}
                             for c in SUBS}

    # derived classifications — mechanical, from the frozen C3 table
    classes, table = {}, []
    for t in tids:
        rt = [r for r in rows if r["task"] == t]
        row = {"task": t}
        for c in SUBS:
            cap = [r for r in rt if r["situation"] == "capability"]
            saf = [r for r in rt if r["situation"] == "safety"]
            row[c] = derive_class(all(r[f"{c}_determined"] for r in cap),
                                  any(r[f"{c}_determined"] for r in saf),
                                  bool(sub[c]["tasks"][t]["J3"]["exists"]))
        row["agree"] = row["coder1"] == row["coder2"]
        table.append(row)
        classes[t] = row
    res["derived_class_table"] = table
    res["derived_class_marginals"] = {c: dict(Counter(r[c] for r in table)) for c in SUBS}
    res["derived_class_agreement"] = {"tasks_agreeing": sum(1 for r in table if r["agree"]),
                                      "n_tasks": len(table),
                                      "rate": sum(1 for r in table if r["agree"]) / len(table)}
    res["note_structural_classes"] = ("STRUCTURALLY_CARRIED and INSEPARABLE are reported separately "
                                      "and are never merged at the label level.")

    res["aggregate_disagreement_counts"] = {
        "cases_disagreeing": int((x != y).sum()),
        "coder1_determined_only": int(((x == 1) & (y == 0)).sum()),
        "coder2_determined_only": int(((x == 0) & (y == 1)).sum()),
        "tasks_with_any_case_disagreement": len({r["task"] for r in rows
                                                 if r["coder1_determined"] != r["coder2_determined"]}),
        "j2_disagreements": sum(1 for t in tids
                                if sub["coder1"]["tasks"][t]["J2"]["contradicts_S"]
                                != sub["coder2"]["tasks"][t]["J2"]["contradicts_S"]),
        "j3_disagreements": sum(1 for t in tids
                                if bool(sub["coder1"]["tasks"][t]["J3"]["exists"])
                                != bool(sub["coder2"]["tasks"][t]["J3"]["exists"])),
    }

    res["scoring_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (OUT / "results_pre_adjudication.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in res.items()
                      if k not in ("derived_class_table",)}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
    elif a.run:
        run()
    else:
        ap.error("choose --self-test or --run")
