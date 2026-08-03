"""Human-triage metrics for LLM candidate audit groups."""

from collections import Counter
from typing import Any


VALID_OUTCOMES = {
    "confirmed_missing_coverage",
    "false_positive",
    "out_of_scope",
    "needs_specification_change",
}


def summarize_triage(records: list[dict[str, Any]]) -> dict[str, Any]:
    outcomes: Counter[str] = Counter()
    tests_added = 0
    seen_fingerprints: set[str] = set()
    for record in records:
        fingerprint = record.get("fingerprint")
        outcome = record.get("outcome")
        if not isinstance(fingerprint, str) or not fingerprint:
            raise ValueError("triage record requires a fingerprint")
        if fingerprint in seen_fingerprints:
            raise ValueError(f"duplicate triage fingerprint: {fingerprint}")
        if outcome not in VALID_OUTCOMES:
            raise ValueError(f"invalid triage outcome: {outcome!r}")
        if not isinstance(record.get("deterministic_test_added"), bool):
            raise ValueError("deterministic_test_added must be boolean")
        seen_fingerprints.add(fingerprint)
        outcomes[outcome] += 1
        tests_added += int(record["deterministic_test_added"])

    reviewed = len(records)
    return {
        "reviewed_count": reviewed,
        "confirmed_count": outcomes["confirmed_missing_coverage"],
        "false_positive_count": outcomes["false_positive"],
        "out_of_scope_count": outcomes["out_of_scope"],
        "needs_specification_change_count": outcomes["needs_specification_change"],
        "deterministic_tests_added": tests_added,
        "confirmation_rate": (
            outcomes["confirmed_missing_coverage"] / reviewed if reviewed else 0.0
        ),
        "false_positive_rate": (
            outcomes["false_positive"] / reviewed if reviewed else 0.0
        ),
        "deterministic_test_yield": tests_added / reviewed if reviewed else 0.0,
    }
