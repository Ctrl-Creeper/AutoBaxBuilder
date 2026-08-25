"""Precision-based sample-size sensitivity for the Round-2 calibration, at case level.

Reliability unit is the case-level determination judgement (binary), two coding
runs, Cohen's kappa. Cases nest in tasks and are correlated within task, because
determination is largely a property of the specification; the design effect is
modelled rather than assumed away.

No rate from Instrument Development Round 1 is used. Marginal rates are
prespecified over a grid. The only empirical input is the corpus distribution of
cases per task, which is a structural property of the dataset and is computed
with the twelve burned tasks excluded.

Generative model, per replicate:
    Z_t ~ N(0,1)                       task-level latent shift
    p_t = sigmoid(logit(p) + tau*Z_t)  task-level determination rate
    A   ~ Bernoulli(kappa)             per case: judgement fixed by the rule
    A=1 -> both runs draw the same Bernoulli(p_t)
    A=0 -> the two runs draw independently from Bernoulli(p_t)
With equal marginals this construction yields population kappa = the target,
which the simulation checks rather than assumes.

kappa-hat is asymptotically normal with variance proportional to 1/n_tasks, so
the required task count is obtained by measuring SD at one anchor and rescaling.
The scaling assumption is verified at a second anchor.
"""

from __future__ import annotations

import json
import math

import numpy as np

CASE_COUNTS = np.array(json.load(open("/tmp/corpus_case_counts.json")))
P_GRID = [0.20, 0.35, 0.50, 0.65, 0.80]
KAPPA_GRID = [0.60, 0.70, 0.80]
TAU_GRID = [0.0, 0.5, 1.0, 1.5]
ANCHOR = 40
REPS = 4000
RNG = np.random.default_rng(20260825)


def icc(p: float, tau: float, n: int = 200_000) -> float:
    """ICC of the determination indicator induced by the task-level shift."""
    if tau == 0:
        return 0.0
    pt = 1 / (1 + np.exp(-(math.log(p / (1 - p)) + tau * RNG.standard_normal(n))))
    return float(pt.var() / (pt.var() + np.mean(pt * (1 - pt))))


def kappa_sd(p: float, kappa: float, tau: float, n_tasks: int, reps: int = REPS) -> tuple[float, float]:
    """Return (mean kappa-hat, SD of kappa-hat) over `reps` replicates."""
    m = RNG.choice(CASE_COUNTS, size=(reps, n_tasks))          # cases per task
    width = int(m.max())
    valid = np.arange(width)[None, None, :] < m[:, :, None]     # ragged -> masked

    z = RNG.standard_normal((reps, n_tasks, 1))
    pt = 1 / (1 + np.exp(-(math.log(p / (1 - p)) + tau * z)))

    agree = RNG.random((reps, n_tasks, width)) < kappa
    base = RNG.random((reps, n_tasks, width)) < pt
    other = RNG.random((reps, n_tasks, width)) < pt
    x1 = base
    x2 = np.where(agree, base, other)

    both = (x1 & x2 & valid).sum(axis=(1, 2))
    neither = (~x1 & ~x2 & valid).sum(axis=(1, 2))
    n = valid.sum(axis=(1, 2))
    r1 = (x1 & valid).sum(axis=(1, 2)) / n
    r2 = (x2 & valid).sum(axis=(1, 2)) / n

    po = (both + neither) / n
    pe = r1 * r2 + (1 - r1) * (1 - r2)
    with np.errstate(divide="ignore", invalid="ignore"):
        k = np.where(pe < 1, (po - pe) / (1 - pe), np.nan)
    k = k[np.isfinite(k)]
    return float(k.mean()), float(k.std(ddof=1))


def required_tasks(sd_at_anchor: float, halfwidth: float) -> int:
    """kappa-hat SD scales as 1/sqrt(n_tasks); solve for the count meeting the target."""
    return math.ceil(ANCHOR * (1.96 * sd_at_anchor / halfwidth) ** 2)


def main() -> None:
    print(f"corpus cases/task: mean {CASE_COUNTS.mean():.2f}, median {np.median(CASE_COUNTS):.0f}, "
          f"n_tasks_available {len(CASE_COUNTS)}  (IDR1 excluded)")
    print(f"anchor n_tasks={ANCHOR}, {REPS} replicates per cell\n")

    print("ICC of the determination indicator induced by tau:")
    for tau in TAU_GRID:
        print(f"  tau={tau:.1f} -> ICC {icc(0.5, tau):.3f} at p=0.50, "
              f"{icc(0.20, tau):.3f} at p=0.20, {icc(0.80, tau):.3f} at p=0.80")
    print()

    # --- verify the 1/sqrt(n) scaling before relying on it
    worst = (0.20, 0.60, 1.5)
    _, sd40 = kappa_sd(*worst, ANCHOR)
    _, sd160 = kappa_sd(*worst, 160)
    print(f"scaling check at p=0.20, kappa=0.60, tau=1.5: "
          f"SD(40)={sd40:.4f}, SD(160)={sd160:.4f}, "
          f"ratio {sd40/sd160:.2f} (expected 2.00)\n")

    rows = []
    for w, label in ((0.10, "w=0.10"), (0.15, "w=0.15")):
        print(f"=== required Round-2 task count for a 95% CI half-width of {w:.2f} on kappa ===")
        print(f"{'kappa':>6} {'tau':>5} " + " ".join(f"{'p='+format(p,'.2f'):>9}" for p in P_GRID))
        for kappa in KAPPA_GRID:
            for tau in TAU_GRID:
                cells = []
                for p in P_GRID:
                    mean_k, sd = kappa_sd(p, kappa, tau, ANCHOR)
                    need = required_tasks(sd, w)
                    cells.append(need)
                    rows.append({"halfwidth": w, "kappa": kappa, "tau": tau, "p": p,
                                 "icc": round(icc(p, tau), 3), "kappa_hat_mean": round(mean_k, 3),
                                 "sd_at_anchor": round(sd, 4), "tasks_required": need,
                                 "cases_required": int(round(need * CASE_COUNTS.mean()))})
                print(f"{kappa:>6.2f} {tau:>5.1f} " + " ".join(f"{c:>9d}" for c in cells))
        print()

    json.dump(rows, open("docs/preregistration/round2_sample_size_sensitivity.json", "w"), indent=2)

    for w in (0.10, 0.15):
        sub = [r for r in rows if r["halfwidth"] == w]
        worst_row = max(sub, key=lambda r: r["tasks_required"])
        print(f"worst cell at w={w:.2f}: kappa={worst_row['kappa']}, tau={worst_row['tau']} "
              f"(ICC {worst_row['icc']}), p={worst_row['p']} -> "
              f"{worst_row['tasks_required']} tasks / ~{worst_row['cases_required']} cases")


if __name__ == "__main__":
    main()
