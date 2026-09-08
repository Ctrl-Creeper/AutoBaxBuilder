#!/usr/bin/env python3
"""Revision-2 consistency audit for the paper synthesis artifacts.

Revision 1's audit (`cross_document_consistency_check.py`) is one-shot and its report exists; it is
preserved unchanged and is not re-run. This audit re-checks everything revision 1 checked, and adds
the checks the Study-4 behavioural line requires:

  * Studies 1-3 claim rows are byte-identical to the revision-1 freeze;
  * frozen Study-4-fresh / 4B / 4C source hashes;
  * the allowed behavioural wording is present, and the Study-4B qualifier is adjacent to the
    Study-4B claim wherever that claim appears;
  * every prohibited overclaim appears only inside a prohibition context, never as an assertion.

Like revision 1, it does not parse any source file containing task-level records.
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
REPORT = HERE / "CROSS_DOCUMENT_CONSISTENCY_REPORT_STUDY4.json"
REVISION_1_COMMIT = "1dda9cf5b3abdca8930900fdc8ac0d92234bb3b8"

DOCS = {
    "matrix": HERE / "paper_claim_evidence_matrix.md",
    "architecture": HERE / "paper_architecture_v1.md",
    "review": HERE / "reviewer_attack_audit.md",
    "decision": HERE / "study4_decision_memo.md",
    "revision": HERE / "SYNTHESIS_REVISION_2_STUDY4.md",
}

FROZEN_SOURCES = {
    "study1_protocol": (
        "docs/preregistration/2026-08-27_study1_prevalence_protocol.md",
        "e4e0833079e68bbb6d4ae14787e38a98d8363518675c5890ec4c7d235f2c5c2b",
    ),
    "study1_results": (
        "docs/preregistration/2026-08-27_study1_execution/results_study1_prevalence.json",
        "dd13be72a3a4e750032d63cef96d3ab68ab1371e2c665d94a442ccc572e81cfe",
    ),
    "study2_protocol_v2": (
        "docs/preregistration/2026-08-25_instrument_validation_protocol_v2.md",
        "4ca61b25973be20beec9cad085a7da503d600fdb7f427eb0e4251c3e02eb45da",
    ),
    "study2_results": (
        "docs/preregistration/2026-08-26_round2_coder_packets/results_pre_adjudication.json",
        "17300bb140cdce38a1d2e38f06adef57775ce7a172f88b5acfef55c18a68427a",
    ),
    "study2_interpretation": (
        "docs/preregistration/2026-08-26_round2_interpretation_memo.md",
        "8aef7785f7a484279111eaf87e957dbffa242574a87eeb8d43543701a0339c3c",
    ),
    "study3_protocol": (
        "docs/preregistration/2026-08-28_study3_constructive_separability_protocol.md",
        "548addbd9277dbe901b8e1e599fdf3a6d4ef97e286610dbecc40bf1f5f5f81d7",
    ),
    "study3_final_summary": (
        "docs/preregistration/2026-08-28_study3_execution/FINAL_STUDY3_RESULT_SUMMARY.json",
        "affc40415afc43246d5c3036e36d1faa03a87fe9ade59b9952c34e375a2b6234",
    ),
    "cweval_termination": (
        "docs/preregistration/2026-08-28_cweval_replication/AMENDMENT_1_gap2_termination.md",
        "fec1aa081de064074c46ef113b4a2c1325970ae3c673e11d0fa1bc5911a30cdc",
    ),
    "study4_fresh_hard_stop": (
        "docs/preregistration/2026-09-07_study4_calibration_execution/CALIBRATION_HARD_STOP.json",
        "4f274f2d5de96ff489010d6f158a6bbed7c3e13f57dc533a6e4cdd0834dc9a3f",
    ),
    "study4b_closure": (
        "docs/preregistration/2026-09-08_study4b_execution/STUDY4B_CLOSURE.md",
        "769e1077d1e0f78b97235c0c4c0c7d5a36a9edfc17990b556dc934ed5d3f8162",
    ),
    "study4b_analysis": (
        "docs/preregistration/2026-09-08_study4b_execution/study4b_analysis_FROZEN.json",
        "5fd37dd6ec0e35370090f8ecb42a955e0fb3e33872356e3b9ef085c42b546cdd",
    ),
    "study4c_results": (
        "docs/preregistration/2026-09-08_study4c_execution/STUDY4C_RESULTS.md",
        "3a5f130d7dceab2e36b6f0c5ef1d7d98174132621144bc9f6bb721ee8e3c8b04",
    ),
    "study4c_analysis": (
        "docs/preregistration/2026-09-08_study4c_execution/study4c_analysis_FROZEN.json",
        "48778c565b521485f99e4a81f9a45d07a811f903d0f8aef28b76d84a41d47203",
    ),
    "study4c_closure_manifest": (
        "docs/preregistration/2026-09-08_study4c_execution/STUDY4C_CLOSURE_MANIFEST.json",
        "5dfc0b08146803aa2a959c87fb5ba36eed04ae42ffaa4c91720253f7c719efa7",
    ),
}

# Claim rows that must not move in revision 2.
UNCHANGED_CLAIM_ROWS = ["C1.", "C2.", "C3.", "C4.", "C5.", "C7.", "C8.", "C10.", "C11.", "C12."]

# Prohibited overclaims. Each pattern may appear only inside a prohibition context.
PROHIBITED = {
    "proves_intrinsic_conflict": r"prove[sd]?\s+(?:an\s+)?intrinsic",
    "proves_collateral_damage": r"prove[sd]?\s+implementation collateral damage",
    "sprime_changes_functional_spec": r"s' changes the functional specification",
    "score_inflation_magnitude": r"\+?50\.5\s*pp",
    "share_attributed_to_generic": r"(?:mostly|largely|entirely|chiefly|predominantly)\s+generic",
    "security_loss_mostly_generic": r"security loss (?:was|is)\s+(?:mostly|largely|entirely)",
    "study4c_invalidates_study3": r"study 4c invalidates study 3",
    "guardrail_invalidates_separability": r"invalidates specification-level separability",
    "capability_held_constant": r"capability was behaviorally held constant",
    "models_exploit": r"models exploit",
    "inflates_scores": r"inflates scores",
    "outcome_naive": r"outcome-naive independent confirmation",
}
PROHIBITION_MARKERS = (
    "forbidden", "not allowed", "do not", "does not", "never", "must not", "cannot",
    "prohibited", "abandoned", "may not", "did not", "is not", "was not", "no ",
)

STUDY4B_CLAIM = (
    "on the frozen 47 demonstrated-separable tasks, model behavior was strongly sensitive to the s "
    "versus s' specification condition: the determining s condition substantially increased "
    "securitypass while substantially reducing capabilitypass."
)
STUDY4B_QUALIFIER = (
    "because capabilitypass also changed substantially, the securitypass contrast cannot be "
    "interpreted as the isolated causal effect of safety-determining information while functional "
    "performance is held constant."
)
STUDY4C_CLAIM = (
    "a matched-control follow-up did not isolate the mechanism underlying the capability shift. "
    "explicit interface-contract reinforcement produced no capability recovery relative to a "
    "length- and structure-matched placebo, while both added-instruction conditions reduced "
    "securitypass relative to s."
)
STUDY4C_PLACEBO = (
    "the placebo demonstrates that a substantial nonspecific added-instruction effect was present."
)
STUDY4C_NARROWED = (
    "the matched placebo demonstrates a substantial nonspecific added-instruction effect on "
    "securitypass, so the s_controlled security loss cannot be interpreted as wholly "
    "contract-content-specific."
)
PRESERVED_DISTINCTION = (
    "study-3 capability-determination preservation is a specification-level construct; study-4b "
    "capabilitypass is a model-performance outcome. a change in the latter does not imply the "
    "former was validated incorrectly."
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def norm(text: str) -> str:
    """Lower-case, whitespace-collapsed, with Markdown blockquote markers, emphasis, and code
    ticks removed, so that a phrase check is insensitive to how the phrase was formatted."""
    stripped = "\n".join(re.sub(r"^\s*>\s?", "", line) for line in text.split("\n"))
    stripped = stripped.replace("*", "").replace("`", "")
    return re.sub(r"\s+", " ", stripped).lower()


def units(text: str) -> list[str]:
    """Table rows and prose paragraphs, whitespace-collapsed, as prohibition scopes."""
    out: list[str] = []
    buffer: list[str] = []
    for line in text.split("\n"):
        if line.startswith("|") or line.startswith(">"):
            if buffer:
                out.append(" ".join(buffer))
                buffer = []
            out.append(line)
        elif not line.strip():
            if buffer:
                out.append(" ".join(buffer))
                buffer = []
        else:
            buffer.append(line.strip())
    if buffer:
        out.append(" ".join(buffer))
    return [norm(u) for u in out]


def claim_row(text: str, marker: str) -> str | None:
    for line in text.split("\n"):
        if line.startswith(f"| **{marker}"):
            return line
    return None


def main() -> None:
    if REPORT.exists():
        raise SystemExit("HARD STOP: revision-2 consistency report already exists; audit is one-shot")

    texts = {name: path.read_text(encoding="utf-8") for name, path in DOCS.items()}
    checks: list[dict[str, object]] = []

    def check(name: str, condition: bool, detail: str) -> None:
        checks.append({"name": name, "pass": bool(condition), "detail": detail})

    # --- structural, carried over from revision 1 -----------------------------
    for name, path in DOCS.items():
        check(f"document_exists:{name}", path.is_file(), path.relative_to(REPO).as_posix())
        check(
            f"non_preregistration_status:{name}",
            "not a preregistration" in texts[name] or "not preregistration" in texts[name],
            "document explicitly marked synthesis/provenance, not preregistration",
        )

    for name, (rel, expected) in FROZEN_SOURCES.items():
        actual = sha256_file(REPO / rel)
        check(f"frozen_source_hash:{name}", actual == expected, f"{actual} == {expected}")

    matrix = texts["matrix"]
    architecture = texts["architecture"]
    review = texts["review"]
    decision = texts["decision"]
    revision = texts["revision"]
    combined = "\n".join(texts.values())
    normalized = norm(combined)

    check("matrix_required_claims", all(f"C{i}." in matrix for i in range(1, 17)),
          "C1-C16 present")
    check("architecture_sections", sum(f"## {i}." in architecture for i in range(1, 9)) == 8,
          "eight numbered paper sections after adding the behavioural section")
    check("review_objections", sum(f"| {i} |" in review for i in range(1, 15)) == 14,
          "fourteen numbered reviewer objections")
    check("decision_three_versions", all(f"## Version {v}:" in decision for v in "ABC"),
          "Versions A, B, and C preserved")
    check("decision_recommends_stop", "Version A: stop now" in decision,
          "the ex ante recommendation is preserved verbatim")
    check("decision_version_a_stands", "**Version A stands.**" in decision,
          "post-decision record confirms the recommendation after execution")

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
        "study4b_security_delta": "+0.5053",
        "study4b_security_ci": "[0.3741, 0.6365]",
        "study4b_capability_delta": "-0.3511",
        "study4b_capability_ci": "[-0.4683, -0.2338]",
        "study4c_mech": "-0.0053",
        "study4c_mech_ci": "[-0.0939, +0.0833]",
        "study4c_repair": "-0.0798",
        "study4c_repair_ci": "[-0.1743, +0.0147]",
        "study4c_preserve": "-0.1702",
        "study4c_preserve_ci": "[-0.2695, -0.0709]",
        "study4c_generic": "-0.0957",
        "study4c_generic_ci": "[-0.1580, -0.0335]",
        "fresh_study4_nogo": "0/160",
    }
    for name, token in required_aggregate_tokens.items():
        check(f"aggregate_token:{name}", token in combined, token)

    # --- revision-1 claims must not have moved --------------------------------
    try:
        for marker in UNCHANGED_CLAIM_ROWS:
            blob = subprocess.check_output(
                ["git", "show", f"{REVISION_1_COMMIT}:docs/paper_synthesis/paper_claim_evidence_matrix.md"],
                cwd=REPO, text=True,
            )
            before = claim_row(blob, marker)
            after = claim_row(matrix, marker)
            check(
                f"studies123_claim_unchanged:{marker.rstrip('.')}",
                before is not None and before == after,
                "byte-identical to the revision-1 freeze",
            )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"HARD STOP: unable to read the revision-1 matrix: {exc}") from exc

    check("revision_records_v1_hashes",
          "e113a00d12d6efef36e38970c3f329b994d795dab4a369f7cb94ca1d20f511f1" in revision
          and REVISION_1_COMMIT in revision,
          "revision record pins the revision-1 commit and document hashes")

    # --- revision-1 semantic checks, re-run -----------------------------------
    check("study3_population_scope",
          "realized measured-eligible confirmatory sample" in combined,
          "47/53 remains conditional on measured eligibility")
    check("vo_zero_interpretation",
          "no obstruction was established" in normalized
          and ("does not mean no obstruction exists" in normalized
               or "not that no obstruction exists" in normalized),
          "VO=0 is certificate failure, not nonexistence")
    check("cweval_no_prevalence",
          "No CWEval Definition-D prevalence" in architecture
          and "not a Definition-D prevalence estimate" in matrix,
          "terminated arm contributes structural portability only")
    check("coding_run_scope",
          "not independent human coders" in norm(matrix)
          and "not independent human coders" in norm(architecture),
          "run-level reliability is not represented as human-coder validation")
    check("study4_no_protocol",
          "No Study-4 protocol is initiated by this memo." in decision,
          "the ex ante memo still initiates no protocol")
    check("matrix_c9_still_unsupported",
          "UNSUPPORTED AS A CAUSAL CLAIM" in matrix,
          "C9 was not upgraded to supported by the behavioural line")

    # --- behavioural-line wording ---------------------------------------------
    check("study4b_allowed_claim_present", STUDY4B_CLAIM in normalized, "Study-4B allowed wording")
    check("study4b_qualifier_present", STUDY4B_QUALIFIER in normalized, "mandatory qualifier")
    check("study4c_allowed_claim_present", STUDY4C_CLAIM in normalized, "Study-4C allowed wording")
    check("study4c_placebo_claim_present", STUDY4C_PLACEBO in normalized, "placebo statement")
    check("study4c_narrowed_statement_present", STUDY4C_NARROWED in normalized,
          "binding narrowed consequence statement")
    check("preserved_distinction_present", PRESERVED_DISTINCTION in normalized,
          "Study-3 vs Study-4B construct distinction")

    # Adjacency: wherever the Study-4B claim appears, the qualifier must follow it closely.
    adjacency_failures = []
    for name, text in texts.items():
        flat = norm(text)
        start = 0
        while True:
            idx = flat.find(STUDY4B_CLAIM, start)
            if idx < 0:
                break
            window = flat[idx: idx + len(STUDY4B_CLAIM) + 1200]
            if STUDY4B_QUALIFIER not in window:
                adjacency_failures.append(name)
            start = idx + 1
    check("study4b_qualifier_adjacent", not adjacency_failures,
          f"unqualified occurrences in: {sorted(set(adjacency_failures)) or 'none'}")

    check("study4b_guardrail_failure_disclosed",
          "failed" in norm(matrix) and "capability guardrail" in norm(matrix)
          and "FAILED" in architecture,
          "the failed capability guardrail is stated, not softened")
    check("study4c_exploratory_grade_disclosed",
          "designed after study 4b" in normalized
          and "negatively conditioned" in normalized,
          "Study 4C is labelled post-4B with its placebo-authoring limitation")
    check("fresh_study4_kept_separate",
          "0/160" in combined
          and ("separate, separately closed" in normalized or "separately closed study" in normalized),
          "fresh Study 4 NO-GO preserved and kept separate from 4B/4C")
    check("no_share_of_effect_attributed",
          "no share or proportion" in normalized or "not identified by this design" in normalized,
          "the nonspecific share is explicitly declared unidentified")
    check("behavioural_line_closed",
          "no study 4d" in normalized and "closed" in normalized,
          "the behavioural experiment line is recorded as closed")

    # --- prohibited overclaims may appear only inside prohibition contexts -----
    assertion_hits: list[dict[str, str]] = []
    for name, text in texts.items():
        for unit in units(text):
            for label, pattern in PROHIBITED.items():
                if re.search(pattern, unit) and not any(m in unit for m in PROHIBITION_MARKERS):
                    assertion_hits.append({"document": name, "pattern": label,
                                           "unit": unit[:220]})
    check("no_prohibited_overclaim_asserted", not assertion_hits,
          f"{len(assertion_hits)} assertive occurrence(s)")

    failures = [item for item in checks if not item["pass"]]
    try:
        base_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"HARD STOP: unable to resolve git HEAD: {exc}") from exc

    report = {
        "schema_version": "paper-synthesis-consistency-v2",
        "status": "PASS" if not failures else "HARD_STOP",
        "document_type": "non-preregistration synthesis audit, revision 2",
        "revision_1_commit": REVISION_1_COMMIT,
        "base_commit": base_commit,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task_level_sources_parsed": False,
        "checks_passed": len(checks) - len(failures),
        "checks_total": len(checks),
        "prohibited_overclaim_assertions": assertion_hits,
        "failures": failures,
        "checks": checks,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"revision-2 cross-document consistency: {report['checks_passed']}/{report['checks_total']} PASS")
    print(f"report: {REPORT.relative_to(REPO)}")
    for item in failures:
        print(f"  FAIL {item['name']}: {item['detail']}")
    if failures:
        raise SystemExit("HARD STOP: cross-document consistency failure")


if __name__ == "__main__":
    main()
