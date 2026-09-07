#!/usr/bin/env python3
"""One-shot consistency audit for the non-preregistered paper synthesis artifacts.

The audit reads the four synthesis documents and hashes frozen source artifacts. It deliberately
does not parse source files that contain task-level records.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
REPORT = HERE / "CROSS_DOCUMENT_CONSISTENCY_REPORT_FINAL_V2.json"

DOCS = {
    "matrix": HERE / "paper_claim_evidence_matrix.md",
    "architecture": HERE / "paper_architecture_v1.md",
    "review": HERE / "reviewer_attack_audit.md",
    "decision": HERE / "study4_decision_memo.md",
}

FROZEN_SOURCES = {
    "study1_protocol": (
        REPO / "docs/preregistration/2026-08-27_study1_prevalence_protocol.md",
        "e4e0833079e68bbb6d4ae14787e38a98d8363518675c5890ec4c7d235f2c5c2b",
    ),
    "study1_results": (
        REPO / "docs/preregistration/2026-08-27_study1_execution/results_study1_prevalence.json",
        "dd13be72a3a4e750032d63cef96d3ab68ab1371e2c665d94a442ccc572e81cfe",
    ),
    "study2_protocol_v2": (
        REPO / "docs/preregistration/2026-08-25_instrument_validation_protocol_v2.md",
        "4ca61b25973be20beec9cad085a7da503d600fdb7f427eb0e4251c3e02eb45da",
    ),
    "study2_results": (
        REPO / "docs/preregistration/2026-08-26_round2_coder_packets/results_pre_adjudication.json",
        "17300bb140cdce38a1d2e38f06adef57775ce7a172f88b5acfef55c18a68427a",
    ),
    "study2_interpretation": (
        REPO / "docs/preregistration/2026-08-26_round2_interpretation_memo.md",
        "8aef7785f7a484279111eaf87e957dbffa242574a87eeb8d43543701a0339c3c",
    ),
    "study3_protocol": (
        REPO / "docs/preregistration/2026-08-28_study3_constructive_separability_protocol.md",
        "548addbd9277dbe901b8e1e599fdf3a6d4ef97e286610dbecc40bf1f5f5f81d7",
    ),
    "study3_final_summary": (
        REPO / "docs/preregistration/2026-08-28_study3_execution/FINAL_STUDY3_RESULT_SUMMARY.json",
        "affc40415afc43246d5c3036e36d1faa03a87fe9ade59b9952c34e375a2b6234",
    ),
    "cweval_termination": (
        REPO / "docs/preregistration/2026-08-28_cweval_replication/AMENDMENT_1_gap2_termination.md",
        "fec1aa081de064074c46ef113b4a2c1325970ae3c673e11d0fa1bc5911a30cdc",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    if REPORT.exists():
        raise SystemExit("HARD STOP: consistency report already exists; this audit is one-shot")

    texts = {name: path.read_text(encoding="utf-8") for name, path in DOCS.items()}
    checks: list[dict[str, object]] = []

    def check(name: str, condition: bool, detail: str) -> None:
        checks.append({"name": name, "pass": bool(condition), "detail": detail})

    for name, path in DOCS.items():
        check(f"document_exists:{name}", path.is_file(), path.relative_to(REPO).as_posix())
        check(
            f"non_preregistration_status:{name}",
            "not a preregistration" in texts[name] or "not preregistration" in texts[name],
            "document explicitly marked synthesis/analytical, not preregistration",
        )

    for name, (path, expected) in FROZEN_SOURCES.items():
        actual = sha256(path)
        check(f"frozen_source_hash:{name}", actual == expected, f"{actual} == {expected}")

    matrix = texts["matrix"]
    architecture = texts["architecture"]
    review = texts["review"]
    decision = texts["decision"]

    check("matrix_required_claims", all(f"C{i}." in matrix for i in range(1, 10)), "C1-C9 present")
    check(
        "matrix_c9_boundary",
        "UNSUPPORTED / REQUIRES STUDY 4" in matrix,
        "behavioral exploitation claim remains unsupported",
    )
    check("architecture_six_sections", sum(f"## {i}." in architecture for i in range(1, 7)) == 6,
          "six numbered paper sections")
    check("review_ten_objections", sum(f"| {i} |" in review for i in range(1, 11)) == 10,
          "ten numbered reviewer objections")
    check("decision_three_versions", all(f"## Version {v}:" in decision for v in "ABC"),
          "Versions A, B, and C present")
    check("decision_recommends_stop", "Version A: stop now" in decision,
          "Study 4 is an enhancement, not a validity prerequisite")

    combined = "\n".join(texts.values())
    normalized = re.sub(r"\s+", " ", combined).lower()
    required_aggregate_tokens = {
        "study1_theta_saf": "0.7805",
        "study1_theta_cap": "0.6899",
        "study1_measurement_interval": "[0.7707, 0.7902]",
        "study2_cluster_kappa": "0.804",
        "study2_cluster_kappa_interval": "[0.708, 0.893]",
        "study3_counts": "DS = 47",
        "study3_vo": "VO = 0",
        "study3_ur": "UR = 6",
        "study3_l0": "[47/53, 1]",
    }
    for name, token in required_aggregate_tokens.items():
        check(f"aggregate_token:{name}", token in combined, token)

    check(
        "study3_population_scope",
        "realized measured-eligible confirmatory sample" in combined,
        "47/53 remains conditional on measured eligibility",
    )
    check(
        "vo_zero_interpretation",
        "no obstruction was established" in normalized
        and (
            "does not mean no obstruction exists" in normalized
            or "not that no obstruction exists" in normalized
        ),
        "VO=0 is certificate failure, not nonexistence",
    )
    check(
        "cweval_no_prevalence",
        "No CWEval Definition-D prevalence" in architecture
        and "not a Definition-D prevalence estimate" in matrix,
        "terminated arm contributes structural portability only",
    )
    check(
        "coding_run_scope",
        "not independent human coders" in re.sub(r"\s+", " ", matrix).lower()
        and "not independent human coders" in re.sub(r"\s+", " ", architecture).lower(),
        "run-level reliability is not represented as human-coder validation",
    )
    check(
        "study4_no_protocol",
        "No Study-4 protocol is initiated by this memo." in decision,
        "decision memo does not initiate a protocol",
    )

    failures = [item for item in checks if not item["pass"]]
    try:
        base_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"HARD STOP: unable to resolve git HEAD: {exc}") from exc

    report = {
        "schema_version": "paper-synthesis-consistency-v1",
        "status": "PASS" if not failures else "HARD_STOP",
        "document_type": "non-preregistration synthesis audit",
        "base_commit": base_commit,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task_level_sources_parsed": False,
        "checks_passed": len(checks) - len(failures),
        "checks_total": len(checks),
        "failures": failures,
        "checks": checks,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"cross-document consistency: {report['checks_passed']}/{report['checks_total']} PASS")
    print(f"report: {REPORT.relative_to(REPO)}")
    if failures:
        raise SystemExit("HARD STOP: cross-document consistency failure")


if __name__ == "__main__":
    main()
