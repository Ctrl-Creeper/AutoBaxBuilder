"""Study 4X-CM design amendment 1 — repeats 2 and 3. See DESIGN_AMENDMENT_1.md.

Reads the frozen repeat-1 artifacts read-only; writes only new files.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import random
import sys
import time
from pathlib import Path
from typing import Any

import study4x_run as r1
from study4x_run import (  # noqa: F401
    CALLS_DIR, CONDITIONS, GENERATION_CONFIG, HERE, MODEL_ID, N_TASKS, ORACLE,
    ORACLE_SHA256, PROMPTS_SHA256, HardStop, api_call, canonical_bytes, ex,
    load_json, prepare, sha256_bytes, sha256_file, verify_hashfile,
    write_new_hashfile, write_new_json,
)

AMENDMENT = HERE / "DESIGN_AMENDMENT_1.md"
AMENDMENT_SHA256 = "ece341398a06f7f20afc0aa834730ddb90e41502f889fc152984a8bd310617f0"
NEW_REPEATS = (2, 3)
ALL_REPEATS = 3
N_NEW = N_TASKS * len(CONDITIONS) * len(NEW_REPEATS)

R1_FROZEN = {
    "study4x_generation_completion_FROZEN.json": "b3ca02adee17b125eed4f8e22456bf3e34de8f3c6169041fc8550a7c80afb22d",
    "study4x_evaluation_FROZEN.json": "4e88e5b726c11a1df0f1ec09c3f3f552c484624c9b8c016bcf4a738f064fc657",
    "study4x_analysis_FROZEN.json": "722827be103a58cd74217d5853c5a8e06708b137046113e4a0a08430c8bb4eeb",
}

GATE_REPORT = HERE / "study4x_r2r3_gate_report_FROZEN.json"
COMPLETION = HERE / "study4x_r2r3_generation_completion_FROZEN.json"
RESPONSE_HASHES = HERE / "SHA256SUMS_RESPONSES_R2R3"
EVALUATION = HERE / "study4x_r2r3_evaluation_FROZEN.json"
POOLED = HERE / "study4x_pooled_analysis_FROZEN.json"
HARD_STOP = HERE / "STUDY4X_R2R3_HARD_STOP.json"


def check_repeat1_intact() -> dict[str, str]:
    """Gates 10-11."""
    for name, expected in R1_FROZEN.items():
        if sha256_file(HERE / name) != expected:
            raise HardStop(f"repeat-1 artifact changed: {name}")
    verify_hashfile(HERE / "SHA256SUMS_RESPONSES")
    existing = {row["request_id"] for row in load_json(HERE / r1.COMPLETION.name)["rows"]}
    if len(existing) != 94:
        raise HardStop("repeat-1 transcripts are incomplete")
    return existing


def schedule(rows: list[dict[str, Any]], existing: set[str]) -> list[dict[str, Any]]:
    units = [
        {
            "request_id": f"{row['ds_task_id']}-{condition}-R{repeat}",
            "ds_task_id": row["ds_task_id"],
            "source_index": row["source_index"],
            "condition": condition,
            "repeat": repeat,
            "prompt_sha256": row[f"{condition}_sha256"],
            "seed": int.from_bytes(
                hashlib.sha256(
                    f"{r1.root_seed(PROMPTS_SHA256)}|{row['ds_task_id']}|{condition}|R{repeat}".encode()
                ).digest()[:4],
                "big",
            ),
        }
        for row in rows
        for condition in CONDITIONS
        for repeat in NEW_REPEATS
    ]
    if {unit["request_id"] for unit in units} & existing:
        raise HardStop("new request_id collides with a frozen repeat-1 transcript")
    r1_seeds = {row["seed"] for row in load_json(r1.COMPLETION)["rows"]}
    if len({unit["seed"] for unit in units}) != len(units) or (
        {unit["seed"] for unit in units} & r1_seeds
    ):
        raise HardStop("derived seeds are not distinct from each other or from repeat 1")
    random.Random(r1.root_seed(PROMPTS_SHA256) ^ 0x52325233).shuffle(units)
    for position, unit in enumerate(units, 1):
        unit["position"] = position
    return units


def gates() -> None:
    if GATE_REPORT.exists():
        raise HardStop("amendment gates are already frozen")
    if sha256_file(AMENDMENT) != AMENDMENT_SHA256:
        raise HardStop("DESIGN_AMENDMENT_1.md changed after freezing")
    if sha256_file(r1.DESIGN) != r1.DESIGN_SHA256:
        raise HardStop("DESIGN_FROZEN.md changed")
    rows = r1.prompt_rows()
    if sha256_file(ORACLE) != ORACLE_SHA256:
        raise HardStop("evaluation oracle hash mismatch")
    prepare.verify_sources()
    existing = check_repeat1_intact()

    models, _ = api_call("/models", None, "models")
    served = sorted(item["id"] for item in models["data"])
    if MODEL_ID not in served:
        raise HardStop(f"{MODEL_ID} is not served by the endpoint")
    smoke, _ = api_call(
        "/chat/completions",
        {
            "model": MODEL_ID,
            "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
            **GENERATION_CONFIG,
            "stream": False,
        },
        "smoke",
    )
    if smoke.get("model") != MODEL_ID or not smoke.get("choices"):
        raise HardStop("smoke call did not return a usable choice from the pinned model")

    write_new_json(
        GATE_REPORT,
        {
            "schema": "study4x-r2r3-gate-report-v1",
            "confirmatory": False,
            "amendment_sha256": AMENDMENT_SHA256,
            "design_sha256": r1.DESIGN_SHA256,
            "gates": {
                "amendment_frozen": "PASS",
                "prompt_projection_hash": "PASS",
                "prompt_completeness_and_per_prompt_hashes": "PASS",
                "prompt_projection_oracle_free": "PASS",
                "evaluation_oracle_hash": "PASS",
                "study3_oracle_provenance": "PASS",
                "model_served": "PASS",
                "smoke_call_with_generation_config": "PASS",
                "api_key_process_local_only": "PASS",
                "repeat1_artifacts_intact": "PASS",
                "no_request_id_or_seed_collision": "PASS",
            },
            "repeat1_hashes": R1_FROZEN,
            "served_model_ids": served,
            "smoke_system_fingerprint": smoke.get("system_fingerprint"),
            "n_requests_planned": N_NEW,
            "schedule": schedule(rows, existing),
        },
    )
    print(f"amendment gates 11/11 GO; sha256 {sha256_file(GATE_REPORT)}", flush=True)


def generate() -> None:
    if COMPLETION.exists():
        raise HardStop("repeat-2/3 generation is already frozen")
    report = load_json(GATE_REPORT)
    if report["amendment_sha256"] != AMENDMENT_SHA256 or sha256_file(AMENDMENT) != AMENDMENT_SHA256:
        raise HardStop("amendment changed after the gates were frozen")
    check_repeat1_intact()
    rows = {row["ds_task_id"]: row for row in r1.prompt_rows()}
    done, records = 0, []
    with concurrent.futures.ThreadPoolExecutor(max_workers=r1.MAX_CONCURRENCY) as pool:
        futures = [
            pool.submit(r1._one_call, unit, rows[unit["ds_task_id"]][unit["condition"]])
            for unit in report["schedule"]
        ]
        for future in concurrent.futures.as_completed(futures):
            records.append(future.result())
            done += 1
            print(f"generate {done:03d}/{N_NEW}", flush=True)
    if len(records) != N_NEW:
        raise HardStop("generation incomplete")
    records.sort(key=lambda record: record["position"])
    finish_reasons: dict[str, int] = {}
    tokens = 0
    for record in records:
        reason = record["response"]["choices"][0].get("finish_reason") or "unknown"
        finish_reasons[reason] = finish_reasons.get(reason, 0) + 1
        tokens += (record["response"].get("usage") or {}).get("completion_tokens", 0)
    write_new_json(
        COMPLETION,
        {
            "schema": "study4x-r2r3-generation-completion-v1",
            "confirmatory": False,
            "gate_report_sha256": sha256_file(GATE_REPORT),
            "model_id": MODEL_ID,
            "endpoint": r1.ENDPOINT,
            "repeats": list(NEW_REPEATS),
            "n_completed": len(records),
            "n_retried_requests": sum(1 for r in records if len(r["attempts"]) > 1),
            "finish_reasons": finish_reasons,
            "total_completion_tokens": tokens,
            "rows": [
                {
                    key: record[key]
                    for key in (
                        "request_id", "ds_task_id", "source_index", "condition",
                        "repeat", "position", "prompt_sha256", "seed",
                    )
                }
                | {"response_sha256": sha256_file(CALLS_DIR / f"{record['request_id']}.json")}
                for record in records
            ],
        },
    )
    write_new_hashfile(
        RESPONSE_HASHES,
        [CALLS_DIR / f"{record['request_id']}.json" for record in records],
    )
    print(f"{len(records)}/{N_NEW} frozen; sha256 {sha256_file(COMPLETION)}", flush=True)


def evaluate() -> None:
    if EVALUATION.exists():
        raise HardStop("repeat-2/3 evaluation is already frozen")
    verify_hashfile(RESPONSE_HASHES)
    check_repeat1_intact()
    completion = load_json(COMPLETION)
    if completion["n_completed"] != N_NEW:
        raise HardStop("generation freeze is incomplete")
    prepare.verify_sources()
    if sha256_file(ORACLE) != ORACLE_SHA256:
        raise HardStop("oracle hash mismatch before evaluation")
    stimuli = load_json(ORACLE)
    benchmark_records = ex._load_benchmark_records(stimuli)
    pairs = {pair["ds_task_id"]: pair for pair in stimuli["pairs"]}

    preflight = []
    for number, pair in enumerate(stimuli["pairs"], 1):
        result = ex.run_program(ex.build_reference_program(benchmark_records[pair["source_index"]]))
        ok = (
            result["status"] == "OK"
            and ex.all_pass(result.get("results"), "capability") == 1
            and ex.all_pass(result.get("results"), "safety") == 1
        )
        preflight.append({"ds_task_id": pair["ds_task_id"], "ok": ok, "status": result["status"]})
        print(f"oracle preflight {number:02d}/{N_TASKS}", flush=True)
    if not all(row["ok"] for row in preflight):
        raise HardStop("frozen evaluator environment failed patched-reference preflight")

    scored = []
    for number, row in enumerate(completion["rows"], 1):
        content = r1.response_content(row["request_id"])
        code = ex.extract_code(content)
        result = ex.run_program(ex.build_generated_program(pairs[row["ds_task_id"]]["execution"], code))
        capability = ex.all_pass(result.get("results"), "capability")
        security = ex.all_pass(result.get("results"), "safety")
        scored.append(
            {
                "request_id": row["request_id"],
                "ds_task_id": row["ds_task_id"],
                "condition": row["condition"],
                "repeat": row["repeat"],
                "runner_status": result["status"],
                "capability_pass": capability,
                "security_pass": security,
                "joint_pass": int(capability and security),
                "empty_response": int(not content.strip()),
                "code_sha256": sha256_bytes(code.encode()),
            }
        )
        print(f"evaluate {number:03d}/{N_NEW}", flush=True)
    prepare.verify_sources()
    write_new_json(
        EVALUATION,
        {
            "schema": "study4x-r2r3-evaluation-v1",
            "confirmatory": False,
            "generation_completion_sha256": sha256_file(COMPLETION),
            "oracle_sha256": ORACLE_SHA256,
            "runner": "completion inserted into frozen SeCodePLT unittest semantics",
            "code_extraction": "first fenced block; otherwise entire response",
            "non_runnable_scoring": "zero on security, capability, and joint endpoints",
            "preflight": preflight,
            "n_evaluated": len(scored),
            "rows": scored,
        },
    )
    print(f"evaluation sha256 {sha256_file(EVALUATION)}", flush=True)


def _category(aggregates: dict[str, Any]) -> str:
    def excludes_zero(name: str) -> bool:
        low, high = aggregates[name]["ci_95"]
        return low > 0 or high < 0

    security, capability = aggregates["security"], aggregates["capability"]
    if excludes_zero("security") and excludes_zero("capability"):
        return (
            "DIRECTIONAL_REPRODUCTION"
            if security["delta"] > 0 and capability["delta"] < 0
            else "OPPOSITE"
        )
    if excludes_zero("security") or excludes_zero("capability"):
        moved, is_security = (
            (security, True) if excludes_zero("security") else (capability, False)
        )
        expected = moved["delta"] > 0 if is_security else moved["delta"] < 0
        return "PARTIAL" if expected else "OPPOSITE"
    return "NO_REPRODUCTION"


def pool() -> None:
    if POOLED.exists():
        raise HardStop("pooled analysis is already frozen")
    check_repeat1_intact()
    rows = load_json(r1.EVALUATION)["rows"] + load_json(EVALUATION)["rows"]
    if len(rows) != N_TASKS * len(CONDITIONS) * ALL_REPEATS:
        raise HardStop("pooled evaluation row count is wrong")
    task_ids = [pair["ds_task_id"] for pair in load_json(ORACLE)["pairs"]]
    pooled = ex.aggregate_endpoints(rows, task_ids, ALL_REPEATS)
    per_repeat = {}
    for repeat in range(1, ALL_REPEATS + 1):
        subset = [dict(row, repeat=1) for row in rows if row["repeat"] == repeat]
        per_repeat[f"R{repeat}"] = ex.aggregate_endpoints(subset, task_ids, 1)
    categories = {name: _category(value) for name, value in per_repeat.items()}
    pooled_category = _category(pooled)
    stability = (
        "STABLE"
        if all(value == pooled_category for value in categories.values())
        else "UNSTABLE"
    )
    write_new_json(
        POOLED,
        {
            "schema": "study4x-pooled-analysis-v1",
            "confirmatory": False,
            "study": "Study 4X-CM cross-model exploratory extension, repeats 1-3",
            "model_id": MODEL_ID,
            "scope": "frozen DS=47 subset only; 3 repeats; single remote model",
            "repeat1_evaluation_sha256": sha256_file(r1.EVALUATION),
            "r2r3_evaluation_sha256": sha256_file(EVALUATION),
            "estimator": "task-equal mean of 47 within-task S-minus-Sprime differences, each condition mean over 3 repeats",
            "confidence_interval": "paired t 95% CI across 47 task differences",
            "p_value": "exact two-sided task-level sign-flip test (descriptive)",
            "pre_declared_readout": pooled_category,
            "pre_declared_stability_readout": stability,
            "per_repeat_readout": categories,
            "aggregates": pooled,
            "per_repeat_aggregates": per_repeat,
            "replicates_study4b": False,
            "comparable_to_ornith_arms": False,
            "subgroup_or_task_failure_mining_performed": False,
        },
    )
    for name in ("security", "capability", "joint"):
        row = pooled[name]
        print(
            f"{name:11s} S={row['rate_S']:.4f} Sprime={row['rate_Sprime']:.4f} "
            f"delta={row['delta']:+.4f} CI=[{row['ci_95'][0]:+.4f},{row['ci_95'][1]:+.4f}] "
            f"p={row['randomization_p_two_sided']:.4g}",
            flush=True,
        )
    print(f"pooled {pooled_category}; stability {stability} {categories}", flush=True)
    print(f"pooled analysis sha256 {sha256_file(POOLED)}", flush=True)


def main() -> None:
    stage = sys.argv[1]
    try:
        {"gates": gates, "generate": generate, "evaluate": evaluate, "pool": pool}[stage]()
    except BaseException as error:
        if isinstance(error, HardStop) and not HARD_STOP.exists():
            write_new_json(
                HARD_STOP, {"stage": stage, "error": str(error), "type": type(error).__name__}
            )
        raise


if __name__ == "__main__":
    main()
