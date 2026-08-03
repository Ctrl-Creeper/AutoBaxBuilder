"""Validation helpers for reference-fixture calibration records."""

from collections import Counter
from typing import Any


VALID_STATUSES = {"pending", "calibrated", "needs_review"}


def _expected_cwes(fixture: dict[str, Any]) -> list[int]:
    values = fixture.get("expected_cwes", [])
    if not isinstance(values, list) or not all(
        isinstance(value, int) for value in values
    ):
        raise ValueError("fixture expected_cwes must be an integer list")
    return sorted(set(values))


def _run_by_fixture(probe: dict[str, Any]) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for run in probe.get("runs", []):
        fixture_id = run.get("fixture_id")
        observed = run.get("observed_cwes")
        if (
            isinstance(fixture_id, str)
            and isinstance(observed, list)
            and all(isinstance(value, int) for value in observed)
        ):
            result[fixture_id] = sorted(set(observed))
    return result


def evaluate_probe(probe: dict[str, Any]) -> dict[str, Any]:
    """Evaluate registry evidence without executing any fixture."""
    probe_id = probe.get("probe_id")
    status = probe.get("status")
    secure = probe.get("secure_fixture")
    vulnerable = probe.get("vulnerable_fixture")
    errors: list[str] = []
    if not isinstance(probe_id, str) or not probe_id:
        errors.append("missing probe_id")
    if status not in VALID_STATUSES:
        errors.append("invalid status")
    if not isinstance(secure, dict) or not isinstance(vulnerable, dict):
        errors.append("missing fixture declarations")
        return {"probe_id": probe_id, "status": "invalid", "errors": errors}

    secure_id = secure.get("id")
    vulnerable_id = vulnerable.get("id")
    if not isinstance(secure_id, str) or not isinstance(vulnerable_id, str):
        errors.append("fixture id must be a string")
    try:
        secure_expected = _expected_cwes(secure)
        vulnerable_expected = _expected_cwes(vulnerable)
    except ValueError as exc:
        errors.append(str(exc))
        secure_expected = []
        vulnerable_expected = []
    if secure_expected:
        errors.append("secure fixture must expect no CWEs")
    if not vulnerable_expected:
        errors.append("vulnerable fixture must expect at least one CWE")

    if status == "pending" and not errors:
        return {"probe_id": probe_id, "status": "pending", "errors": []}
    if status == "needs_review" and not errors:
        return {"probe_id": probe_id, "status": "needs_review", "errors": []}

    observed = _run_by_fixture(probe)
    if observed.get(secure_id) != secure_expected:
        errors.append("secure fixture evidence is missing or does not match")
    if observed.get(vulnerable_id) != vulnerable_expected:
        errors.append("vulnerable fixture evidence is missing or does not match")
    return {
        "probe_id": probe_id,
        "status": "calibrated" if not errors else "invalid",
        "errors": errors,
    }


def summarize_calibration(registry: dict[str, Any]) -> dict[str, Any]:
    rows = [evaluate_probe(probe) for probe in registry.get("probes", [])]
    counts = Counter(row["status"] for row in rows)
    return {
        "benchmark_version": registry.get("benchmark_version"),
        "total_probes": len(rows),
        "calibrated_count": counts["calibrated"],
        "pending_count": counts["pending"],
        "needs_review_count": counts["needs_review"],
        "invalid_count": counts["invalid"],
        "rows": rows,
    }
