#!/usr/bin/env python3
"""Synthetic contract tests for the independent final Study-3 audit."""

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
AUDITOR = HERE / "audit_final_study3.py"


def load_auditor():
    if not AUDITOR.is_file():
        raise AssertionError("independent final audit tool is missing")
    spec = importlib.util.spec_from_file_location("audit_final_study3", AUDITOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def fixtures() -> tuple[dict, dict, dict, dict, dict]:
    eligibility = {
        "n_drawn": 3,
        "m": 3,
        "eligible_task_ids": ["P01", "P02", "P03"],
        "eligible_indices": {"P01": 101, "P02": 102, "P03": 103},
        "either_agree_count_sensitivity_only": 4,
    }
    ds = {
        "task_index": {"Q01": 101, "Q02": 102, "Q03": 103},
        "per_task": {
            "Q01": {"ds_both_runs": True, "ds_either_run_sensitivity_only": True},
            "Q02": {"ds_both_runs": False, "ds_either_run_sensitivity_only": True},
            "Q03": {"ds_both_runs": False, "ds_either_run_sensitivity_only": False},
        },
    }
    vo = {
        "vo_tasks": {"P02": {"class": "VO-STRUCT"}},
        "rejected_claims": [],
    }
    vo_provenance = {
        "vo_defect": {
            "status": "PERMANENTLY_CLOSED",
            "input_directory_present": False,
            "certificate_files_present": 0,
            "attestation_files_present": 0,
        }
    }
    result = {
        "m_measured_eligible": 3,
        "classification": {
            "per_task": {"P01": "DS", "P02": "VO", "P03": "UR"},
            "counts": {"DS": 1, "VO": 1, "UR": 1},
            "shares": {"P_hat_DS": 1 / 3, "P_hat_VO": 1 / 3, "P_hat_UR": 1 / 3},
        },
        "L0_sample_identification_region": {
            "region": [1 / 3, 2 / 3],
            "statement": "sample identification region; NOT a confidence interval",
        },
        "L1_sampling_clopper_pearson": {
            "pi_ds_cp95": [0.008403758659612638, 0.9057006759497539],
            "pi_vo_cp95": [0.008403758659612638, 0.9057006759497539],
            "conditional_on_m": 3,
            "targets": "separate endpoints only",
        },
        "L2_measurement_sensitivity": {
            "ds_either_run_share_sensitivity_only": 2 / 3,
            "ds_both_runs_definition_share": 1 / 3,
            "eligibility_both_agree_m": 3,
            "eligibility_either_agree_count_sensitivity_only": 4,
            "note": "sensitivity descriptives only",
        },
        "descriptive": {
            "procedure_invalid_candidate": {"count": 0, "task_ids": []},
        },
    }
    return result, eligibility, ds, vo, vo_provenance


def run_audit(*, mutate_result=None, mutate_ds=None, mutate_vo=None,
              mutate_vo_provenance=None, resolver_state="FORMAL_RUN2_ACCEPTED",
              mutate_source=None) -> dict:
    auditor = load_auditor()
    result, eligibility, ds, vo, vo_provenance = fixtures()
    if mutate_result:
        mutate_result(result)
    if mutate_ds:
        mutate_ds(ds)
    if mutate_vo:
        mutate_vo(vo)
    if mutate_vo_provenance:
        mutate_vo_provenance(vo_provenance)
    source = (HERE / "score_study3.py").read_text()
    if mutate_source:
        source = mutate_source(source)
    return auditor.audit_result_contract(
        result, eligibility, ds, vo, vo_provenance, source, resolver_state)


class FinalAuditTests(unittest.TestCase):
    def test_valid_synthetic_result_passes_all_sixteen_contract_checks(self) -> None:
        report = run_audit()
        self.assertEqual(report["pass_count"], 16)
        self.assertEqual(report["fail_count"], 0)

    def test_wrong_classification_count_is_rejected(self) -> None:
        report = run_audit(mutate_result=lambda r: r["classification"]["counts"].update(DS=2))
        self.assertGreater(report["fail_count"], 0)

    def test_ds_vo_overlap_is_rejected(self) -> None:
        report = run_audit(mutate_vo=lambda v: v["vo_tasks"].update(
            {"P01": {"class": "VO-STRUCT"}}))
        self.assertFalse(report["checks"]["09_ds_vo_overlap_zero"])

    def test_nonzero_procedure_invalid_is_rejected(self) -> None:
        def mutate(result):
            result["descriptive"]["procedure_invalid_candidate"] = {
                "count": 1, "task_ids": ["P03"]}
        report = run_audit(mutate_result=mutate)
        self.assertFalse(report["checks"]["10_procedure_invalid_zero"])

    def test_wrong_cp_endpoint_is_rejected(self) -> None:
        def mutate(result):
            result["L1_sampling_clopper_pearson"]["pi_ds_cp95"][0] = 0.1
        report = run_audit(mutate_result=mutate)
        self.assertFalse(report["checks"]["11_cp_endpoints_match_frozen_definition"])

    def test_wrong_l2_value_is_rejected(self) -> None:
        def mutate(result):
            result["L2_measurement_sensitivity"][
                "ds_either_run_share_sensitivity_only"] = 0.5
        report = run_audit(mutate_result=mutate)
        self.assertFalse(report["checks"]["12_l2_matches_frozen_rule"])

    def test_combined_interval_is_rejected(self) -> None:
        report = run_audit(mutate_result=lambda r: r.update(combined_interval=[0, 1]))
        self.assertFalse(report["checks"]["13_no_combined_or_posthoc_interval"])

    def test_open_vo_defect_path_is_rejected(self) -> None:
        report = run_audit(mutate_vo_provenance=lambda p: p["vo_defect"].update(
            status="OPEN"))
        self.assertFalse(report["checks"]["14_vo_defect_not_executed"])

    def test_changed_substantive_function_is_rejected(self) -> None:
        report = run_audit(mutate_source=lambda s: s.replace(
            'return "DS" if ds else "VO" if vo else "UR"',
            'return "VO" if ds else "DS" if vo else "UR"'))
        self.assertFalse(report["checks"]["15_substantive_function_hashes_unchanged"])

    def test_wrong_formal_resolver_state_is_rejected(self) -> None:
        report = run_audit(resolver_state="FORMAL_PROCEDURE_INVALID")
        self.assertFalse(report["checks"]["16_formal_state_is_run2_accepted"])


if __name__ == "__main__":
    unittest.main()
