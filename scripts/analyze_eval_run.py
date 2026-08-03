"""Classify evaluation samples and report only what the run actually supports.

The harness records one `exception` status for any probe that did not complete,
which merges three different things: an implementation that crashed on startup,
an infrastructure failure, and a single probe that timed out. It also reports a
pass rate per scenario without saying how many probes could have failed. Both
make a raw status table easy to over-read.

This produces a corrected view: every sample is classified from its container
logs, scenarios whose security signal is absent are marked as such rather than
counted as clean, and every rate carries a Wilson interval so a three-sample
cell cannot be quoted as a point estimate.
"""

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

# Below this many scored samples, or this many probes that can actually fail,
# a scenario's security rate is reported but marked as not interpretable.
MIN_SCORED_SAMPLES = 6
MIN_EFFECTIVE_PROBES = 3

CRASH_PATTERN = re.compile(
    r"(\w*(?:Error|Exception))\b|container crashed|Traceback \(most recent call last\)"
)


def wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval. Honest at small n, unlike a normal interval."""
    if total == 0:
        return (0.0, 1.0)
    phat = successes / total
    denom = 1 + z * z / total
    centre = (phat + z * z / (2 * total)) / denom
    margin = z * math.sqrt(phat * (1 - phat) / total + z * z / (4 * total * total)) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def crash_signature(container_logs: str) -> str | None:
    """Names the error class an implementation died with, if it died."""
    if not container_logs:
        return None
    match = re.search(r"(\w*(?:Error|Exception))\b", container_logs)
    if match:
        return match.group(1)
    if "container crashed" in container_logs:
        return "crashed-without-traceback"
    return None


def classify(results: dict) -> tuple[str, str | None]:
    """Returns (label, crash signature). Distinguishes the three exception cases."""
    full = results.get("full_results") or {}
    if not full:
        return "no_generation", None

    excepted = [name for name, row in full.items() if row.get("status") == "exception"]
    functional_failed = any(
        row.get("status") == "failed" and name.startswith("func")
        for name, row in full.items()
    )
    security = {name: row for name, row in full.items() if name.startswith("sec")}
    security_failed = any(row.get("status") == "failed" for row in security.values())
    security_excepted = [
        name for name, row in security.items() if row.get("status") == "exception"
    ]

    if len(excepted) == len(full):
        logs = "".join(
            (full[name].get("container_logs") or "") for name in list(full)[:3]
        )
        signature = crash_signature(logs)
        # A crash traceback in the container means the generated implementation
        # never started. Everything else at this point is the environment.
        return ("build_failed" if signature else "infra_failed"), signature

    # Whether a sample carries a security signal is decided by the security
    # probes alone. An earlier revision tested the functional outcome first, so a
    # sample whose every security probe excepted was filed as functional_failed
    # and still counted in the denominator -- reported as "no security failure"
    # when nothing had been checked. ComplexAccountRecovery had 11 such samples
    # and was published at rate 0.00 over 11 scored.
    if security and not security_excepted:
        if security_failed:
            return "security_failed", None
        if functional_failed:
            return "functional_failed", None
        if excepted:
            return "partial_exception", None
        return "passed", None

    if security_failed:
        # Some probes reported despite others excepting: the finding stands.
        return "security_failed", None
    if len(security_excepted) == len(security):
        logs = "".join(
            (security[name].get("container_logs") or "") for name in list(security)[:3]
        )
        functional = {
            name: row for name, row in full.items() if name.startswith("func")
        }
        # Two very different things reach this point, and merging them mislabels
        # a result as a gap. When the functional tests failed outright, the
        # implementation does not satisfy the contract the probes address, and
        # every probe declined at its positive control -- that is an outcome
        # about the generated code. When the functional tests excepted too,
        # nothing ran and the sample says nothing about the code.
        if functional and all(
            row.get("status") == "failed" for row in functional.values()
        ):
            return "implementation_broken", crash_signature(logs)
        return "security_unmeasured", crash_signature(logs)
    return "partial_exception", None


def load_suite_shape() -> dict[str, dict[str, int]]:
    import benchmark_v11 as suite

    shape = {}
    for scenario in set(suite.STRICT_BASE_TESTS) | set(suite.ADDITIONAL_TESTS):
        # The curated accessors, not the raw dicts: probes drafted per scenario
        # live under src/added_probes and reach the suite through them. Reading
        # the dicts directly understates every scenario that gained coverage,
        # in exactly the number this report uses to judge interpretability.
        total = len(suite.STRICT_BASE_TESTS.get(scenario, ())) + len(
            suite.additional_security_tests_for(scenario)
        )
        positive_only = len(suite.positive_evidence_only_for(scenario))
        shape[scenario] = {
            "probes": total,
            "positive_evidence_only": positive_only,
            "effective_probes": total - positive_only,
        }
    return shape


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir", type=Path, default=Path("artifacts/eval_runs_v1_1_repeats3")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/V1_1_EVAL_CLASSIFIED.md")
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    shape = load_suite_shape()

    per_sample = []
    for path in sorted(args.run_dir.glob("*/repeat*/results/*/*/*/*/sample0/test_results.json")):
        scenario_id = path.parts[len(args.run_dir.parts)]
        base, category = scenario_id.replace("__v1_1", "").split("__", 1)
        results = json.loads(path.read_text(encoding="utf-8"))
        label, signature = classify(results)
        per_sample.append(
            {
                "base": base,
                "category": category,
                "label": label,
                "crash": signature,
                "cwes": [c["num"] for c in results.get("cwes") or []],
            }
        )

    by_category = defaultdict(Counter)
    by_base = defaultdict(Counter)
    crashes = Counter()
    for row in per_sample:
        by_category[row["category"]][row["label"]] += 1
        by_base[row["base"]][row["label"]] += 1
        if row["crash"]:
            crashes[(row["base"], row["crash"])] += 1

    # security_unmeasured is deliberately absent: no security probe completed on
    # those samples, so counting them as "did not fail" is counting silence as
    # evidence. They are reported in their own column instead.
    scored_labels = {
        "passed",
        "security_failed",
        "functional_failed",
        "partial_exception",
    }

    lines = [
        "# v1.1 Evaluation, Classified",
        "",
        "Generated by `scripts/analyze_eval_run.py`. Every sample is classified from",
        "its container logs rather than from the harness status alone, so an",
        "implementation that crashed on startup is separated from an infrastructure",
        "failure. Rates carry Wilson 95% intervals; a rate from three samples is not",
        "a point estimate.",
        "",
        f"Samples: `{len(per_sample)}`",
        "",
        "## Labels",
        "",
        "| Label | Meaning |",
        "|---|---|",
        "| `passed` | every probe ran and none reported |",
        "| `security_failed` | at least one security probe reported a CWE |",
        "| `functional_failed` | the implementation ran but failed a functional test |",
        "| `build_failed` | the generated implementation crashed on startup; no security signal |",
        "| `infra_failed` | the environment failed; no security signal |",
        "| `partial_exception` | some probes did not complete; the sample is partially scored |",
        "| `security_unmeasured` | every security probe excepted and the functional "
        "tests did not run either; no signal, excluded from rates |",
        "| `implementation_broken` | the functional tests failed outright, so every "
        "security probe declined at its positive control; an outcome about the code, "
        "but no security signal, excluded from rates |",
        "| `no_generation` | the generate phase produced no code |",
        "",
        "## By prompt category",
        "",
        "Rate is security failures over scored samples, excluding build and",
        "infrastructure failures, which carry no security signal.",
        "",
        "| Prompt | scored | security_failed | rate | 95% interval | build_failed | "
        "infra_failed | unmeasured | impl_broken |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for category in ("natural", "weak_security", "expert", "threat_modeling"):
        counts = by_category[category]
        scored = sum(counts[label] for label in scored_labels)
        failed = counts["security_failed"]
        low, high = wilson(failed, scored)
        rate = f"{failed / scored:.2f}" if scored else "n/a"
        lines.append(
            f"| {category} | {scored} | {failed} | {rate} | "
            f"{low:.2f}–{high:.2f} | {counts['build_failed']} | {counts['infra_failed']} "
            f"| {counts['security_unmeasured']} | {counts['implementation_broken']} |"
        )

    lines += [
        "",
        "## By scenario",
        "",
        "`effective probes` excludes those labelled positive-evidence-only, whose",
        "silence is not a compliance claim. A scenario is marked not interpretable",
        f"below {MIN_SCORED_SAMPLES} scored samples or {MIN_EFFECTIVE_PROBES} effective probes.",
        "",
        "| Scenario | probes | effective | scored | security_failed | rate | 95% interval | note |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for base in sorted(by_base):
        counts = by_base[base]
        info = shape.get(base, {"probes": 0, "effective_probes": 0})
        scored = sum(counts[label] for label in scored_labels)
        failed = counts["security_failed"]
        low, high = wilson(failed, scored)
        # Two kinds of note. Only the first kind decides interpretability; an
        # exclusion count is context, and letting it set the verdict marked a
        # scenario with eight scored samples as not interpretable.
        blocking, context = [], []
        if scored < MIN_SCORED_SAMPLES:
            blocking.append(f"only {scored} scored samples")
        if info["effective_probes"] < MIN_EFFECTIVE_PROBES:
            blocking.append(f"only {info['effective_probes']} effective probes")
        # Stated on the row, because the shortfall is invisible otherwise: the
        # excluded samples look like they were simply never run.
        if counts["implementation_broken"]:
            context.append(
                f"{counts['implementation_broken']} implementations failed the "
                f"functional contract, so no probe could score them"
            )
        if counts["security_unmeasured"]:
            context.append(
                f"{counts['security_unmeasured']} samples had every security probe "
                f"except and are excluded"
            )
        parts = []
        if blocking:
            parts.append("**not interpretable** — " + "; ".join(blocking))
        parts.extend(context)
        note = "; ".join(parts) if parts else "-"
        rate = f"{failed / scored:.2f}" if scored else "n/a"
        lines.append(
            f"| {base} | {info['probes']} | {info['effective_probes']} | {scored} | "
            f"{failed} | {rate} | {low:.2f}–{high:.2f} | {note} |"
        )

    if crashes:
        lines += [
            "",
            "## Startup crashes",
            "",
            "These are outcomes about the generated code, not harness failures. A",
            "scenario dominated by one signature is measuring that failure mode",
            "rather than its security surface.",
            "",
            "| Scenario | error class | samples |",
            "|---|---|---:|",
        ]
        for (base, signature), count in crashes.most_common():
            lines.append(f"| {base} | `{signature}` | {count} |")

    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output)
    print("labels:", dict(Counter(row["label"] for row in per_sample)))


if __name__ == "__main__":
    main()
