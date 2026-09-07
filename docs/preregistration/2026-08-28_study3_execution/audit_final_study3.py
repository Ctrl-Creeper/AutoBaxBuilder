#!/usr/bin/env python3
"""Independent arithmetic and contract audit for the frozen Study-3 result.

This tool intentionally does not import score_study3 or any scorer helper.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

from scipy import stats


HERE = Path(__file__).resolve().parent
OUT = HERE / "FINAL_STUDY3_ARITHMETIC_CONTRACT_AUDIT.json"

EXPECTED_SCORER_SHA256 = "0ed4fd477d233881c699f2b497a03e79e5358ad681c294cd0feae5e94a53b415"
EXPECTED_GAP8_AMENDMENT_MANIFEST_SHA256 = (
    "8eb434d1b0ed5a9f2f82c2a8e3d65c2a2766e32334fb804b8bb746f4c5e7deb5")
EXPECTED_FUNCTION_SHA256 = {
    "cp_interval": "7525022292ad3693b063b5b9a814a3705330d1c3abc3f130ffd0844dd52bcf4a",
    "map_ds_to_baseline": "0d7659e562c868dd217f9129a9c568d9f9444acbb95e2d393b917feeb3456b74",
    "classify": "d7dd69b6e933f229904c136737c470a68253a823aa2a791331322f3e3a0f4aff",
    "score": "51e2e4cdb394a8a07506309bd9c1cf0bdb82b5182f8da3979345ef88fc3582e6",
}
FORMAL_PINS = {
    "writer_handoff/GATE_UNREPAIRABLE_FROZEN.json":
        "357e241ea030ee598f8a091a4f9dacc2947f1f5de9249a9f1ce189cecf19f4c4",
    "GAP6_writer_instrument_contract_audit.md":
        "a5ac01698990a04a6a9cd6d67dd6bc54d851f19de0a951172c91d7ea2f9a167c",
    "GAP6_REPAIR_RECORD.md":
        "a52fc7ee3704ae265dfc37dac860487969c848f91f3a43ba5f4146d1675b8dca",
    "writer_handoff/WRITER_RUN2_TERMINAL_STATE.md":
        "ee64173d1479c8a143f9acd9eedc9466c8181f3c618bd29f84ea8367c3ae4545",
    "writer_handoff/submissions/writer_output_ACCEPT_FIRST_RUN2.json":
        "f2b0e73ab1d8b5efcb22bb53c2b8d026446994992195d9b55b483d8de593b49e",
    "sprime_packet_build_provenance.json":
        "0a6565a4b85a41362b5df0e8995327e232f9b657fc4260f46ac758e1f18642c5",
    "ds_derivation.json":
        "3377d187c2c37177f37e1c9b5d648b34468d10bd4239404b971888c835e4efe7",
    "vo_certificates.json":
        "cd2cc35b269a1d27d9093462685eae09ace6dc07d9fec95002f9cba55d3c0060",
    "VO_STRUCT_EXECUTION_PROVENANCE.json":
        "9059365a44633831e509eb0a514def18c5f5ae075fe12410a8c5b3c88ce23d46",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(left: float, right: float) -> bool:
    return abs(left - right) <= 1e-12


def cp_interval(k: int, n: int) -> list[float]:
    if n == 0:
        return [0.0, 1.0]
    low = 0.0 if k == 0 else float(stats.beta.ppf(0.025, k, n - k + 1))
    high = 1.0 if k == n else float(stats.beta.ppf(0.975, k + 1, n - k))
    return [low, high]


def function_hashes(source: str) -> dict[str, str]:
    tree = ast.parse(source)
    hashes = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in EXPECTED_FUNCTION_SHA256:
            raw = ast.get_source_segment(source, node).encode()
            hashes[node.name] = hashlib.sha256(raw).hexdigest()
    return hashes


def independent_formal_state(here: Path) -> str:
    scorer = here / "score_study3.py"
    amendment_manifest = here / "SHA256SUMS_GAP8_AMENDMENT"
    if sha256_file(scorer) != EXPECTED_SCORER_SHA256:
        sys.exit("HARD STOP - independent audit found a scorer hash mismatch")
    if sha256_file(amendment_manifest) != EXPECTED_GAP8_AMENDMENT_MANIFEST_SHA256:
        sys.exit("HARD STOP - independent audit found a GAP-8 manifest mismatch")
    for rel, expected in FORMAL_PINS.items():
        path = here / rel
        if not path.is_file() or sha256_file(path) != expected:
            sys.exit(f"HARD STOP - independent formal-state pin failed: {rel}")

    gate = json.loads((here / "writer_handoff/GATE_UNREPAIRABLE_FROZEN.json").read_text())
    gap6 = (here / "GAP6_REPAIR_RECORD.md").read_text()
    run2 = (here / "writer_handoff/WRITER_RUN2_TERMINAL_STATE.md").read_text()
    sprime = json.loads((here / "sprime_packet_build_provenance.json").read_text())
    vo_provenance = json.loads((here / "VO_STRUCT_EXECUTION_PROVENANCE.json").read_text())
    writer = sprime.get("authoritative_writer_input", {})
    closed = vo_provenance.get("vo_defect", {})
    statuses_ok = (
        gate.get("verdict") == "UNREPAIRABLE_FIRST_SUBMISSION"
        and "WRITER_INSTRUMENT_CONTRACT_FAILURE" in gap6
        and "Run 1 enters no DS/VO/UR identification result" in gap6
        and "Status: **ACCEPT_FIRST_RUN2**" in run2
        and writer == {
            "path": "writer_handoff/submissions/writer_output_ACCEPT_FIRST_RUN2.json",
            "terminal_state": "ACCEPT_FIRST_RUN2",
            "sha256": FORMAL_PINS[
                "writer_handoff/submissions/writer_output_ACCEPT_FIRST_RUN2.json"],
            "sole_constructive_input": True,
        }
        and closed.get("status") == "PERMANENTLY_CLOSED"
        and closed.get("input_directory_present") is False
        and closed.get("certificate_files_present") == 0
        and closed.get("attestation_files_present") == 0
        and not (here / "vo_defect").exists()
    )
    if not statuses_ok:
        sys.exit("HARD STOP - independent formal-state status check failed")
    return "FORMAL_RUN2_ACCEPTED"


def audit_result_contract(result: dict, eligibility: dict, ds: dict, vo: dict,
                          vo_provenance: dict, scorer_source: str,
                          resolver_state: str, expected_m: int | None = None) -> dict:
    m = eligibility["m"]
    expected_m = m if expected_m is None else expected_m
    eligible_ids = eligibility["eligible_task_ids"]
    idx_to_q = {index: qid for qid, index in ds["task_index"].items()}
    ds_by_task = {
        tid: ds["per_task"][idx_to_q[eligibility["eligible_indices"][tid]]]
        for tid in eligible_ids
    }
    ds_ids = {tid for tid, entry in ds_by_task.items() if entry["ds_both_runs"]}
    vo_ids = set(vo["vo_tasks"])
    overlap = ds_ids & vo_ids
    expected_per_task = {
        tid: "DS" if tid in ds_ids else "VO" if tid in vo_ids else "UR"
        for tid in eligible_ids
    }
    expected_counts = {
        name: sum(value == name for value in expected_per_task.values())
        for name in ("DS", "VO", "UR")
    }

    classification = result["classification"]
    counts = classification["counts"]
    per_task = classification["per_task"]
    l0 = result["L0_sample_identification_region"]["region"]
    l1 = result["L1_sampling_clopper_pearson"]
    l2 = result["L2_measurement_sensitivity"]
    procedure_invalid = result["descriptive"]["procedure_invalid_candidate"]["count"]
    expected_l = expected_counts["DS"] / m
    expected_u = 1 - expected_counts["VO"] / m
    expected_cp_ds = cp_interval(expected_counts["DS"], m)
    expected_cp_vo = cp_interval(expected_counts["VO"], m)
    expected_l2_either = sum(
        entry["ds_either_run_sensitivity_only"] for entry in ds_by_task.values()) / m

    def same_pair(actual: list[float], expected: list[float]) -> bool:
        return len(actual) == 2 and all(close(a, b) for a, b in zip(actual, expected))

    def all_keys(value) -> list[str]:
        if isinstance(value, dict):
            return [str(key) for key in value] + [
                key for child in value.values() for key in all_keys(child)]
        if isinstance(value, list):
            return [key for child in value for key in all_keys(child)]
        return []

    keys = [key.lower() for key in all_keys(result)]
    l1_keys = {"pi_ds_cp95", "pi_vo_cp95", "conditional_on_m", "targets"}
    closed = vo_provenance.get("vo_defect", {})
    actual_hashes = function_hashes(scorer_source)
    checks = {
        "01_m_matches_frozen_denominator":
            m == expected_m == result["m_measured_eligible"] == len(eligible_ids),
        "02_ds_count_matches_frozen_derivation":
            counts["DS"] == expected_counts["DS"]
            and {tid for tid, value in per_task.items() if value == "DS"} == ds_ids,
        "03_vo_count_matches_frozen_derivation":
            counts["VO"] == expected_counts["VO"]
            and {tid for tid, value in per_task.items() if value == "VO"} == vo_ids,
        "04_ur_count_matches_complement": counts["UR"] == expected_counts["UR"],
        "05_classification_is_exhaustive":
            sum(counts.values()) == m and set(per_task) == set(eligible_ids),
        "06_classification_is_mutually_exclusive":
            set(per_task.values()) <= {"DS", "VO", "UR"}
            and per_task == expected_per_task,
        "07_lower_endpoint_is_ds_over_m": close(l0[0], expected_l),
        "08_upper_endpoint_is_one_minus_vo_over_m": close(l0[1], expected_u),
        "09_ds_vo_overlap_zero": len(overlap) == 0,
        "10_procedure_invalid_zero": procedure_invalid == 0,
        "11_cp_endpoints_match_frozen_definition":
            same_pair(l1["pi_ds_cp95"], expected_cp_ds)
            and same_pair(l1["pi_vo_cp95"], expected_cp_vo)
            and l1["conditional_on_m"] == m,
        "12_l2_matches_frozen_rule":
            close(l2["ds_either_run_share_sensitivity_only"], expected_l2_either)
            and close(l2["ds_both_runs_definition_share"], expected_l)
            and l2["eligibility_both_agree_m"] == m
            and l2["eligibility_either_agree_count_sensitivity_only"]
            == eligibility["either_agree_count_sensitivity_only"],
        "13_no_combined_or_posthoc_interval":
            set(l1) == l1_keys
            and not any(any(term in key for term in
                            ("bootstrap", "imbens", "combined", "overall")) for key in keys),
        "14_vo_defect_not_executed":
            closed.get("status") == "PERMANENTLY_CLOSED"
            and closed.get("input_directory_present") is False
            and closed.get("certificate_files_present") == 0
            and closed.get("attestation_files_present") == 0,
        "15_substantive_function_hashes_unchanged": actual_hashes == EXPECTED_FUNCTION_SHA256,
        "16_formal_state_is_run2_accepted": resolver_state == "FORMAL_RUN2_ACCEPTED",
    }
    return {
        "schema_version": "study3-final-independent-audit-v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "pass_count": sum(checks.values()),
        "fail_count": sum(not value for value in checks.values()),
        "observed_aggregates": {
            "m": m,
            "counts": counts,
            "l0_sample_identification_region": l0,
            "l1_endpoint_intervals": {
                "pi_ds_cp95": l1["pi_ds_cp95"],
                "pi_vo_cp95": l1["pi_vo_cp95"],
            },
            "l2_measurement_sensitivity": l2,
            "ds_vo_overlap_count": len(overlap),
            "procedure_invalid_count": procedure_invalid,
        },
        "independence": {
            "imports_score_study3": False,
            "uses_scorer_helpers": False,
            "prints_task_ids": False,
        },
        "substantive_function_hashes": actual_hashes,
        "resolver_formal_state": resolver_state,
    }


def main() -> None:
    if OUT.exists():
        sys.exit("HARD STOP - final independent audit output already exists")
    required = (
        "results_study3.json", "eligibility_study3.json", "ds_derivation.json",
        "vo_certificates.json", "VO_STRUCT_EXECUTION_PROVENANCE.json", "score_study3.py",
    )
    if not all((HERE / name).is_file() for name in required):
        sys.exit("HARD STOP - final independent audit input is missing")
    formal_state = independent_formal_state(HERE)
    report = audit_result_contract(
        json.loads((HERE / "results_study3.json").read_text()),
        json.loads((HERE / "eligibility_study3.json").read_text()),
        json.loads((HERE / "ds_derivation.json").read_text()),
        json.loads((HERE / "vo_certificates.json").read_text()),
        json.loads((HERE / "VO_STRUCT_EXECUTION_PROVENANCE.json").read_text()),
        (HERE / "score_study3.py").read_text(),
        formal_state,
        expected_m=53,
    )
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(f"independent audit: {report['pass_count']}/16 PASS")
    print(f"audit sha256: {sha256_file(OUT)}")
    if report["fail_count"]:
        sys.exit("HARD STOP - final independent arithmetic/contract audit failed")


if __name__ == "__main__":
    main()
