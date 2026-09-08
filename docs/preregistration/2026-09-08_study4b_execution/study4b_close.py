#!/usr/bin/env python3
"""Mechanical closure and verification for the Study-4B confirmatory line.

`close` derives every reported number from the already-frozen Study-4B artifacts
and writes a closure manifest plus checksums. `verify` re-derives the same values
and fails if any frozen artifact, count, or endpoint has moved.

Nothing here re-runs the model, re-scores completions, or touches Studies 1-3 or
docs/paper_synthesis/.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

EXECUTION_FREEZE = HERE / "study4b_execution_manifest_FROZEN.json"
SCHEDULE = HERE / "study4b_request_schedule_FROZEN.json"
GENERATION = HERE / "study4b_generation_completion_FROZEN.json"
EVALUATION = HERE / "study4b_evaluation_FROZEN.json"
ANALYSIS = HERE / "study4b_analysis_FROZEN.json"
CLOSURE = HERE / "STUDY4B_CLOSURE_MANIFEST.json"
CLOSURE_HASHES = HERE / "SHA256SUMS_CLOSURE"
CALLS_DIR = HERE / "generation_calls"

UPSTREAM_HASHFILES = (
    "SHA256SUMS_READINESS",
    "SHA256SUMS_EXECUTION_FREEZE",
    "SHA256SUMS_RESPONSES",
    "SHA256SUMS_EVALUATION",
    "SHA256SUMS_ANALYSIS",
)

N_TASKS = 47
N_REQUESTS = 376
CAPABILITY_EQUIVALENCE_MARGIN = 0.05

# Interpretation text frozen verbatim at closure. Not editable by later analysis.
ALLOWED = [
    "On the 47 frozen Study-3 demonstrated-separable tasks, the model was "
    "substantially more likely to pass the security oracle under the original "
    "determining specification than under the frozen underdetermined "
    "specification.",
    "However, the specification manipulation also produced a large "
    "capability-performance difference, despite capability determination having "
    "been preserved at the specification level. Therefore the observed security "
    "contrast cannot be interpreted as an isolated causal effect of removing "
    "safety-determining information while holding functional behavior constant.",
]
NOT_ALLOWED = [
    "determination causes +50.5pp security score inflation",
    "removing safety information alone causes the effect",
    "capability was behaviorally held constant",
    "the effect generalizes to SeCodePLT",
    "Study 4B rescues or replaces the failed fresh Study 4",
    "Study 3 was invalidated by the capability guardrail failure",
]
PRESERVED_DISTINCTION = (
    "Study-3 capability-determination preservation is a specification-level "
    "construct; Study-4B CapabilityPass is a model-performance outcome. A change "
    "in the latter does not imply the former was validated incorrectly."
)


class ClosureError(RuntimeError):
    """A mechanical inconsistency that forbids closing Study 4B."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def check_upstream_hashfiles() -> dict[str, str]:
    status = {}
    for name in UPSTREAM_HASHFILES:
        path = HERE / name
        if not path.is_file():
            raise ClosureError(f"missing upstream checksum file: {name}")
        result = subprocess.run(
            ["shasum", "-a", "256", "-c", name],
            cwd=HERE,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise ClosureError(f"upstream checksum verification failed: {name}")
        status[name] = "OK"
    return status


def derive_counts() -> dict[str, Any]:
    generation = load(GENERATION)
    evaluation = load(EVALUATION)
    rows = generation["rows"]
    scored = evaluation["rows"]

    if generation["n_completed"] != N_REQUESTS:
        raise ClosureError("generation is not 376/376")
    if evaluation["n_evaluated"] != N_REQUESTS:
        raise ClosureError("evaluation is not 376/376")
    if len({row["request_id"] for row in rows}) != N_REQUESTS:
        raise ClosureError("request IDs are not unique")
    if {row["request_id"] for row in rows} != {row["request_id"] for row in scored}:
        raise ClosureError("generation and evaluation request sets differ")

    non_runnable = [row for row in scored if row["runner_status"] != "OK"]
    truncated = [row for row in rows if row["finish_reason"] == "length"]
    return {
        "generations_completed": generation["n_completed"],
        "generations_planned": N_REQUESTS,
        "requests_with_retry": generation["requests_with_retry"],
        "total_transport_attempts": generation["total_transport_attempts"],
        "transport_failures": 0,
        "empty_completions": sum(not row["content_present"] for row in rows),
        "non_runnable_total": len(non_runnable),
        "non_runnable_by_condition": {
            condition: sum(row["condition"] == condition for row in non_runnable)
            for condition in ("S", "Sprime")
        },
        "non_runnable_scoring": evaluation["non_runnable_scoring"],
        "max_token_truncations_total": len(truncated),
        "max_token_truncations_by_condition": {
            condition: sum(row["condition"] == condition for row in truncated)
            for condition in ("S", "Sprime")
        },
        "oracle_preflight_pass": sum(item["ok"] for item in evaluation["preflight"]),
        "oracle_preflight_total": len(evaluation["preflight"]),
        "response_artifacts_on_disk": len(list(CALLS_DIR.glob("*/response.json"))),
        "request_artifacts_on_disk": len(list(CALLS_DIR.glob("*/request.json"))),
    }


def derive_endpoints() -> dict[str, Any]:
    aggregates = load(ANALYSIS)["aggregates"]
    table = {}
    for endpoint in ("security", "capability", "joint"):
        block = aggregates[endpoint]
        if len(block["task_differences"]) != N_TASKS:
            raise ClosureError(f"{endpoint} does not have 47 task differences")
        table[endpoint] = {
            "rate_S": block["rate_S"],
            "rate_Sprime": block["rate_Sprime"],
            "delta": block["delta"],
            "ci_95": block["ci_95"],
            "task_difference_sd": block["task_difference_sd"],
            "randomization_p_two_sided": block["randomization_p_two_sided"],
        }
    return table


def guardrail_status(endpoints: dict[str, Any]) -> dict[str, Any]:
    capability = endpoints["capability"]
    inside = abs(capability["delta"]) < CAPABILITY_EQUIVALENCE_MARGIN
    low, high = capability["ci_95"]
    return {
        "endpoint": "CapabilityPass",
        "preregistered_equivalence_margin_pp": CAPABILITY_EQUIVALENCE_MARGIN * 100,
        "observed_delta": capability["delta"],
        "observed_ci_95": capability["ci_95"],
        "point_estimate_inside_margin": inside,
        "ci_excludes_zero": not (low <= 0 <= high),
        "status": "PASS" if inside else "FAILED",
    }


def build_closure() -> dict[str, Any]:
    upstream = check_upstream_hashfiles()
    counts = derive_counts()
    endpoints = derive_endpoints()
    guardrail = guardrail_status(endpoints)

    if guardrail["status"] != "FAILED":
        raise ClosureError("capability guardrail status is not the frozen FAILED value")
    if counts["non_runnable_total"] != 7 or counts["non_runnable_by_condition"]["Sprime"] != 0:
        raise ClosureError("non-runnable count/condition split moved")
    if counts["max_token_truncations_total"] != 1:
        raise ClosureError("max-token truncation count moved")
    if counts["requests_with_retry"] != 0:
        raise ClosureError("retry count moved")
    if counts["oracle_preflight_pass"] != N_TASKS:
        raise ClosureError("oracle preflight is not 47/47")
    if (HERE / "STUDY4B_HARD_STOP.json").exists():
        raise ClosureError("a hard-stop record exists")

    return {
        "schema": "study4b-closure-v1",
        "status": "CLOSED",
        "line": "Study 4B confirmatory behavioral follow-up",
        "scope": "Study-3 frozen demonstrated-separable subset (DS=47) only",
        "study_boundaries": {
            "fresh_sample_study4": {
                "result": "0/160 validated pairs; NO-GO before behavioral evaluation",
                "status": "separately closed",
                "artifacts": "docs/preregistration/2026-09-07_study4_calibration_execution/",
            },
            "study4b_is_not_a_continuation_or_replacement": True,
            "studies_1_to_3_unmodified": True,
            "paper_synthesis_unmodified": True,
        },
        "frozen_artifacts_sha256": {
            path.name: sha256_file(path)
            for path in (
                HERE / "study4b_prepare.py",
                HERE / "test_study4b_prepare.py",
                HERE / "study4b_execute.py",
                HERE / "test_study4b_execute.py",
                HERE / "study4b_readiness_manifest.json",
                HERE / "study4b_ds47_stimuli_SEALED.json",
                HERE / "study4b_generation_stimuli_FROZEN.json",
                SCHEDULE,
                EXECUTION_FREEZE,
                GENERATION,
                EVALUATION,
                ANALYSIS,
            )
        },
        "artifacts_held_on_disk_only": {
            "reason": (
                "sealed stimuli carry the frozen hidden tests/oracle and "
                "generation_calls carry full specification prompts; both enter "
                "git as checksums only, matching the Study-3 convention"
            ),
            "paths": [
                "study4b_ds47_stimuli_SEALED.json",
                "study4b_generation_stimuli_FROZEN.json",
                "generation_calls/",
            ],
            "response_set_sha256": load(GENERATION)["response_set_sha256"],
        },
        "upstream_checksum_verification": upstream,
        "execution_record": counts,
        "endpoints": endpoints,
        "capability_guardrail": guardrail,
        "procedural_deviations": [],
        "hard_stops": [],
        "interpretation": {
            "allowed": ALLOWED,
            "not_allowed": NOT_ALLOWED,
            "preserved_distinction": PRESERVED_DISTINCTION,
            "post_hoc_analysis_may_not_alter_this_block": True,
        },
        "analyses_not_performed_at_closure": [
            "subgroup analysis",
            "task-level failure analysis",
            "completion-content taxonomy",
            "explanation mining",
        ],
        "git": {
            "head_at_closure": subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=HERE, capture_output=True, text=True
            ).stdout.strip(),
            "branch": subprocess.run(
                ["git", "branch", "--show-current"], cwd=HERE, capture_output=True, text=True
            ).stdout.strip(),
        },
    }


def close() -> None:
    if CLOSURE.exists() or CLOSURE_HASHES.exists():
        raise ClosureError("Study-4B closure is already frozen")
    manifest = build_closure()
    CLOSURE.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    targets = [
        HERE / name for name in UPSTREAM_HASHFILES
    ] + [
        EXECUTION_FREEZE,
        SCHEDULE,
        GENERATION,
        EVALUATION,
        ANALYSIS,
        HERE / "study4b_prepare.py",
        HERE / "study4b_execute.py",
        HERE / "study4b_close.py",
        CLOSURE,
    ]
    lines = [f"{sha256_file(path)}  {path.name}" for path in targets]
    CLOSURE_HASHES.write_text("\n".join(lines) + "\n")
    print(f"closure manifest sha256 {sha256_file(CLOSURE)}")
    print(f"capability guardrail {manifest['capability_guardrail']['status']}")


def verify() -> None:
    if not CLOSURE.is_file() or not CLOSURE_HASHES.is_file():
        raise ClosureError("Study-4B closure is absent")
    result = subprocess.run(
        ["shasum", "-a", "256", "-c", CLOSURE_HASHES.name],
        cwd=HERE,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ClosureError(f"closure checksum verification failed:\n{result.stdout}")
    frozen = load(CLOSURE)
    rebuilt = build_closure()
    for field in ("execution_record", "endpoints", "capability_guardrail", "interpretation"):
        if frozen[field] != rebuilt[field]:
            raise ClosureError(f"closure field drifted from frozen artifacts: {field}")
    for name, digest in frozen["frozen_artifacts_sha256"].items():
        if sha256_file(HERE / name) != digest:
            raise ClosureError(f"frozen artifact changed: {name}")
    print("closure verification OK")
    print(f"capability guardrail {frozen['capability_guardrail']['status']}")


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if command not in {"close", "verify"}:
        raise SystemExit("usage: study4b_close.py [close|verify]")
    try:
        close() if command == "close" else verify()
    except ClosureError as exc:
        print(f"CLOSURE ERROR: {exc}", file=sys.stderr)
        raise SystemExit(3) from exc


if __name__ == "__main__":
    main()
