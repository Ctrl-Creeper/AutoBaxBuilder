"""Estimand–estimator audit for Study 3's three-layer inference — synthetic fixtures.

Design under audit: one SRSWOR draw of N=90 tasks from a finite frame (M≈740), a
stochastic measured-eligibility screen (both-runs-agree baseline), then a stochastic
DS/VO/UR outcome per eligible task. Primary descriptive result is the in-sample
interval [P̂(DS), 1−P̂(VO)] over measured-eligible tasks.

Questions answered by simulation, not by convention:

  Q1  Exactness of the in-sample identification statement: with A-DS/A-VO holding
      (no false witness, no false certificate), does the measured-eligible sample's
      true separable share lie inside [P̂(DS), 1−P̂(VO)] in EVERY replication?
      And does an A-DS violation break it (negative fixture)?
  Q2  Which per-endpoint sampling CI attains ≥ nominal coverage for the population
      quantities π_DS = P(DS|eligible), π_VO = P(VO|eligible) across scenarios,
      including the π_VO = 0 boundary and a low-yield (small m) scenario?
      Candidates: Clopper–Pearson conditional on m; percentile bootstrap over the
      90 drawn tasks (re-screening included in the resample).
  Q3  Does a default Imbens–Manski combined interval for σ = P(Sep=1|eligible),
      built from bootstrap endpoint SEs, attain nominal coverage under THIS design
      — in particular at the VO boundary? (Adoption requires demonstrated coverage;
      failure anywhere disqualifies the default.)

All layers are kept separate; nothing here merges them into one headline interval.
Runs offline, deterministic seed, no benchmark data touched.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy import stats

R = 2000          # replications per scenario
B = 400           # bootstrap resamples per replication
N = 90            # frozen CR-1 draw size
M = 740           # approximate frozen frame size (audit realism only)
SEED = 20260828
OUT = Path(__file__).resolve().parent

# Task types: (share, p_eligible_measured, outcome probs given eligible, Sep truth)
# Outcome probs are (p_DS, p_VO, p_UR); A-DS/A-VO hold: DS only if Sep=1, VO only if Sep=0.
SCENARIOS = {
    "A_interior": [
        ("sep_easy", 0.40, 0.85, (0.85, 0.00, 0.15), 1),
        ("insep_struct", 0.15, 0.85, (0.00, 0.80, 0.20), 0),
        ("sep_hard_ur", 0.20, 0.85, (0.10, 0.00, 0.90), 1),
        ("insep_ur", 0.10, 0.85, (0.00, 0.05, 0.95), 0),
        ("not_eligible", 0.15, 0.05, (0.00, 0.00, 1.00), 1),
    ],
    "B_vo_boundary": [
        ("sep_easy", 0.55, 0.85, (0.80, 0.00, 0.20), 1),
        ("sep_hard_ur", 0.30, 0.85, (0.05, 0.00, 0.95), 1),
        ("not_eligible", 0.15, 0.05, (0.00, 0.00, 1.00), 1),
    ],
    "C_low_yield": [
        ("sep_easy", 0.15, 0.75, (0.85, 0.00, 0.15), 1),
        ("insep_struct", 0.10, 0.75, (0.00, 0.75, 0.25), 0),
        ("not_eligible", 0.75, 0.03, (0.00, 0.00, 1.00), 1),
    ],
    "D_high_ds": [
        ("sep_easy", 0.70, 0.90, (0.90, 0.00, 0.10), 1),
        ("insep_struct", 0.10, 0.90, (0.00, 0.85, 0.15), 0),
        ("not_eligible", 0.20, 0.05, (0.00, 0.00, 1.00), 1),
    ],
}


def population_targets(spec):
    """pi_DS, pi_VO, sigma = P(Sep=1 | eligible), all under the measurement process."""
    pe = sum(s * e for _, s, e, _, _ in spec)
    pi_ds = sum(s * e * o[0] for _, s, e, o, _ in spec) / pe
    pi_vo = sum(s * e * o[1] for _, s, e, o, _ in spec) / pe
    sigma = sum(s * e * sep for _, s, e, _, sep in spec) / pe
    return pi_ds, pi_vo, sigma


def build_frame(spec, rng):
    counts = [int(round(s * M)) for _, s, _, _, _ in spec]
    counts[-1] += M - sum(counts)
    types = np.repeat(np.arange(len(spec)), counts)
    rng.shuffle(types)
    return types


def screen_and_measure(types, spec, rng):
    """Stochastic eligibility + outcome for a vector of drawn task types."""
    e_p = np.array([spec[t][2] for t in types])
    elig = rng.random(len(types)) < e_p
    out = np.full(len(types), -1)          # -1 ineligible; 0 DS, 1 VO, 2 UR
    for i in np.flatnonzero(elig):
        out[i] = rng.choice(3, p=spec[types[i]][3])
    sep = np.array([spec[t][4] for t in types])
    return elig, out, sep


def cp_interval(k, n):
    if n == 0:
        return (0.0, 1.0)
    lo = 0.0 if k == 0 else stats.beta.ppf(0.025, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.ppf(0.975, k + 1, n - k)
    return (lo, hi)


def im_interval(p_ds, p_vo, se_l, se_u, m):
    """Imbens–Manski for sigma with estimated endpoint SEs (bootstrap)."""
    lo, up = p_ds, 1 - p_vo
    width = up - lo
    smax = max(se_l, se_u, 1e-12)
    f = lambda c: stats.norm.cdf(c + width / smax) - stats.norm.cdf(-c) - 0.95
    a, b = 0.0, 5.0
    for _ in range(60):
        mid = (a + b) / 2
        if f(mid) < 0:
            a = mid
        else:
            b = mid
    c = (a + b) / 2
    return (max(0.0, lo - c * se_l), min(1.0, up + c * se_u))


def run_scenario(name, spec, rng, ads_violation=0.0):
    pi_ds, pi_vo, sigma = population_targets(spec)
    frame = build_frame(spec, rng)
    cov = {"cp_ds": 0, "cp_vo": 0, "boot_ds": 0, "boot_vo": 0, "im_sigma": 0,
           "insample_exact": 0, "m_sum": 0}
    for _ in range(R):
        draw = rng.choice(M, size=N, replace=False)
        types = frame[draw]
        elig, out, sep = screen_and_measure(types, spec, rng)
        if ads_violation > 0:                     # negative fixture: false witnesses
            for i in np.flatnonzero((out == 2) & (sep == 0)):
                if rng.random() < ads_violation:
                    out[i] = 0
        m = int(elig.sum())
        cov["m_sum"] += m
        if m == 0:
            continue
        k_ds, k_vo = int((out == 0).sum()), int((out == 1).sum())
        p_ds, p_vo = k_ds / m, k_vo / m

        true_insample = sep[elig].mean()
        if p_ds - 1e-12 <= true_insample <= 1 - p_vo + 1e-12:
            cov["insample_exact"] += 1

        lo, hi = cp_interval(k_ds, m)
        cov["cp_ds"] += lo <= pi_ds <= hi
        lo, hi = cp_interval(k_vo, m)
        cov["cp_vo"] += lo <= pi_vo <= hi

        bds, bvo = [], []
        for _ in range(B):
            idx = rng.integers(0, N, N)
            e_b, o_b = elig[idx], out[idx]
            mb = e_b.sum()
            if mb == 0:
                continue
            bds.append((o_b == 0).sum() / mb)
            bvo.append((o_b == 1).sum() / mb)
        bds, bvo = np.array(bds), np.array(bvo)
        cov["boot_ds"] += np.percentile(bds, 2.5) <= pi_ds <= np.percentile(bds, 97.5)
        cov["boot_vo"] += np.percentile(bvo, 2.5) <= pi_vo <= np.percentile(bvo, 97.5)

        lo, hi = im_interval(p_ds, p_vo, bds.std(ddof=1), bvo.std(ddof=1), m)
        cov["im_sigma"] += lo <= sigma <= hi

    res = {"targets": {"pi_ds": pi_ds, "pi_vo": pi_vo, "sigma": sigma},
           "mean_eligible_m": cov["m_sum"] / R,
           "insample_containment_rate": cov["insample_exact"] / R,
           "coverage": {k: cov[k] / R for k in
                        ("cp_ds", "cp_vo", "boot_ds", "boot_vo", "im_sigma")}}
    print(f"{name}: m̄={res['mean_eligible_m']:.1f}  targets πDS={pi_ds:.3f} πVO={pi_vo:.3f} "
          f"σ={sigma:.3f}")
    print(f"  in-sample containment {res['insample_containment_rate']:.4f}")
    print(f"  coverage  CP: DS {res['coverage']['cp_ds']:.3f} VO {res['coverage']['cp_vo']:.3f}"
          f"   boot: DS {res['coverage']['boot_ds']:.3f} VO {res['coverage']['boot_vo']:.3f}"
          f"   IM(σ): {res['coverage']['im_sigma']:.3f}")
    return res


def main() -> None:
    rng = np.random.default_rng(SEED)
    results = {}
    for name, spec in SCENARIOS.items():
        results[name] = run_scenario(name, spec, rng)
    # Negative fixture: a mostly-inseparable population with a 50% false-witness rate.
    # A-DS fails hard, so P̂(DS) should exceed the true in-sample separable share and
    # the containment statement should break — demonstrating it is assumption-bearing.
    neg_spec = [
        ("insep_ur", 0.85, 0.85, (0.00, 0.00, 1.00), 0),
        ("sep_easy", 0.15, 0.85, (0.85, 0.00, 0.15), 1),
    ]
    print("\nnegative fixture: A-DS violated (50% false witnesses, mostly-inseparable frame)")
    results["NEG_ads_violation"] = run_scenario("NEG_ads_violation", neg_spec, rng,
                                                ads_violation=0.5)
    (OUT / "study3_inference_audit_results.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
