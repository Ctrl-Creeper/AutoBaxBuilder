"""Study 4X-CM design amendment 2 — second model arm `gpt-5.6-sol`.

See DESIGN_AMENDMENT_2.md. Reads the frozen luna-arm artifacts read-only and
writes this arm's transcripts to a separate directory.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import random
import sys
import time
from pathlib import Path
from typing import Any

import study4x_repeats as r23
import study4x_run as r1
from study4x_run import (
    CONDITIONS, GENERATION_CONFIG, HERE, N_TASKS, ORACLE, ORACLE_SHA256,
    PROMPTS_SHA256, HardStop, api_call, ex, load_json, prepare, sha256_bytes,
    sha256_file, verify_hashfile, write_new_hashfile, write_new_json,
)

AMENDMENT = HERE / "DESIGN_AMENDMENT_2.md"
AMENDMENT_SHA256 = "79d3f57951f61e0f01b36a7a88e6e18c9c35372739340e56bf8bde1d5be20271"
MODEL_ID = "gpt-5.6-sol"
REPEATS = 3
N_REQUESTS = N_TASKS * len(CONDITIONS) * REPEATS
CALLS_DIR = HERE / "generation_calls_sol"

LUNA_FROZEN = {
    "study4x_generation_completion_FROZEN.json": "b3ca02adee17b125eed4f8e22456bf3e34de8f3c6169041fc8550a7c80afb22d",
    "study4x_evaluation_FROZEN.json": "4e88e5b726c11a1df0f1ec09c3f3f552c484624c9b8c016bcf4a738f064fc657",
    "study4x_analysis_FROZEN.json": "722827be103a58cd74217d5853c5a8e06708b137046113e4a0a08430c8bb4eeb",
    "study4x_r2r3_generation_completion_FROZEN.json": "31de1e394d52662024c58b6548f2122c273bb008a81b0a279bce657e8f8aad28",
    "study4x_r2r3_evaluation_FROZEN.json": "fc3a05dfb522efa97c801d08cc894c33d3af8e101ca6b37b2ca8b780def2e7e2",
    "study4x_pooled_analysis_FROZEN.json": "d5136dd90939f2ac7ffc40943e6b13828d25705e44082d4cb87f84ec48874b9c",
}

GATE_REPORT = HERE / "study4x_sol_gate_report_FROZEN.json"
COMPLETION = HERE / "study4x_sol_generation_completion_FROZEN.json"
RESPONSE_HASHES = HERE / "SHA256SUMS_RESPONSES_SOL"
EVALUATION = HERE / "study4x_sol_evaluation_FROZEN.json"
ANALYSIS = HERE / "study4x_sol_analysis_FROZEN.json"
HARD_STOP = HERE / "STUDY4X_SOL_HARD_STOP.json"


def root_seed() -> int:
    domain = f"study4x-crossmodel-v1|{PROMPTS_SHA256}|{MODEL_ID}"
    return int.from_bytes(hashlib.sha256(domain.encode()).digest()[:8], "big")


def check_luna_intact() -> None:
    """Gate 10."""
    for name, expected in LUNA_FROZEN.items():
        if sha256_file(HERE / name) != expected:
            raise HardStop(f"luna-arm artifact changed: {name}")
    verify_hashfile(HERE / "SHA256SUMS_RESPONSES")
    verify_hashfile(HERE / "SHA256SUMS_RESPONSES_R2R3")


def schedule(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                    f"{root_seed()}|{row['ds_task_id']}|{condition}|R{repeat}".encode()
                ).digest()[:4],
                "big",
            ),
        }
        for row in rows
        for condition in CONDITIONS
        for repeat in range(1, REPEATS + 1)
    ]
    if len({unit["seed"] for unit in units}) != len(units):
        raise HardStop("derived seeds are not distinct within this arm")
    random.Random(root_seed()).shuffle(units)
    for position, unit in enumerate(units, 1):
        unit["position"] = position
    return units


def gates() -> None:
    if GATE_REPORT.exists():
        raise HardStop("sol-arm gates are already frozen")
    if sha256_file(AMENDMENT) != AMENDMENT_SHA256:
        raise HardStop("DESIGN_AMENDMENT_2.md changed after freezing")
    if sha256_file(r1.DESIGN) != r1.DESIGN_SHA256:
        raise HardStop("DESIGN_FROZEN.md changed")
    if sha256_file(r23.AMENDMENT) != r23.AMENDMENT_SHA256:
        raise HardStop("DESIGN_AMENDMENT_1.md changed")
    rows = r1.prompt_rows()
    if sha256_file(ORACLE) != ORACLE_SHA256:
        raise HardStop("evaluation oracle hash mismatch")
    prepare.verify_sources()
    check_luna_intact()
    if CALLS_DIR.exists() and any(CALLS_DIR.iterdir()):
        raise HardStop("sol transcript directory is not empty")
    if CALLS_DIR.resolve() == r1.CALLS_DIR.resolve():
        raise HardStop("sol transcript directory collides with the luna arm")

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
            "schema": "study4x-sol-gate-report-v1",
            "confirmatory": False,
            "amendment_sha256": AMENDMENT_SHA256,
            "design_sha256": r1.DESIGN_SHA256,
            "amendment_1_sha256": r23.AMENDMENT_SHA256,
            "model_id": MODEL_ID,
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
                "luna_arm_artifacts_intact": "PASS",
                "separate_empty_transcript_directory": "PASS",
            },
            "luna_hashes": LUNA_FROZEN,
            "served_model_ids": served,
            "smoke_system_fingerprint": smoke.get("system_fingerprint"),
            "generation_config": GENERATION_CONFIG,
            "n_requests_planned": N_REQUESTS,
            "randomization_root_seed": root_seed(),
            "schedule": schedule(rows),
        },
    )
    print(f"sol gates 11/11 GO; sha256 {sha256_file(GATE_REPORT)}", flush=True)


def _one_call(unit: dict[str, Any], prompt: str) -> dict[str, Any]:
    path = CALLS_DIR / f"{unit['request_id']}.json"
    if path.is_file():
        return load_json(path)
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        **GENERATION_CONFIG,
        "seed": unit["seed"],
        "stream": False,
    }
    started = time.time()
    response, attempts = api_call("/chat/completions", payload, unit["request_id"])
    if response.get("model") != MODEL_ID:
        raise HardStop(f"returned model drift for {unit['request_id']}: {response.get('model')}")
    if not response.get("choices"):
        raise HardStop(f"response without a choice for {unit['request_id']}")
    record = {
        key: unit[key]
        for key in (
            "request_id", "ds_task_id", "source_index", "condition",
            "repeat", "position", "prompt_sha256", "seed",
        )
    } | {
        "model_id": MODEL_ID,
        "attempts": attempts,
        "elapsed_seconds": round(time.time() - started, 3),
        "response": response,
    }
    path.write_bytes(ex.canonical_bytes(record))
    return record


def generate() -> None:
    if COMPLETION.exists():
        raise HardStop("sol-arm generation is already frozen")
    report = load_json(GATE_REPORT)
    if report["amendment_sha256"] != AMENDMENT_SHA256 or sha256_file(AMENDMENT) != AMENDMENT_SHA256:
        raise HardStop("amendment changed after the gates were frozen")
    check_luna_intact()
    rows = {row["ds_task_id"]: row for row in r1.prompt_rows()}
    CALLS_DIR.mkdir(exist_ok=True)
    done, records = 0, []
    with concurrent.futures.ThreadPoolExecutor(max_workers=r1.MAX_CONCURRENCY) as pool:
        futures = [
            pool.submit(_one_call, unit, rows[unit["ds_task_id"]][unit["condition"]])
            for unit in report["schedule"]
        ]
        for future in concurrent.futures.as_completed(futures):
            records.append(future.result())
            done += 1
            print(f"generate {done:03d}/{N_REQUESTS}", flush=True)
    if len(records) != N_REQUESTS:
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
            "schema": "study4x-sol-generation-completion-v1",
            "confirmatory": False,
            "gate_report_sha256": sha256_file(GATE_REPORT),
            "model_id": MODEL_ID,
            "endpoint": r1.ENDPOINT,
            "repeats": REPEATS,
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
    print(f"{len(records)}/{N_REQUESTS} frozen; sha256 {sha256_file(COMPLETION)}", flush=True)


def response_content(request_id: str) -> str:
    record = load_json(CALLS_DIR / f"{request_id}.json")
    message = record["response"]["choices"][0].get("message") or {}
    return message.get("content") or ""


def evaluate() -> None:
    if EVALUATION.exists():
        raise HardStop("sol-arm evaluation is already frozen")
    verify_hashfile(RESPONSE_HASHES)
    check_luna_intact()
    completion = load_json(COMPLETION)
    if completion["n_completed"] != N_REQUESTS:
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
        content = response_content(row["request_id"])
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
        print(f"evaluate {number:03d}/{N_REQUESTS}", flush=True)
    prepare.verify_sources()
    write_new_json(
        EVALUATION,
        {
            "schema": "study4x-sol-evaluation-v1",
            "confirmatory": False,
            "model_id": MODEL_ID,
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


def analyze() -> None:
    if ANALYSIS.exists():
        raise HardStop("sol-arm analysis is already frozen")
    check_luna_intact()
    rows = load_json(EVALUATION)["rows"]
    if len(rows) != N_REQUESTS:
        raise HardStop("evaluation is incomplete")
    task_ids = [pair["ds_task_id"] for pair in load_json(ORACLE)["pairs"]]
    pooled = ex.aggregate_endpoints(rows, task_ids, REPEATS)
    per_repeat = {
        f"R{repeat}": ex.aggregate_endpoints(
            [dict(row, repeat=1) for row in rows if row["repeat"] == repeat], task_ids, 1
        )
        for repeat in range(1, REPEATS + 1)
    }
    categories = {name: r23._category(value) for name, value in per_repeat.items()}
    pooled_category = r23._category(pooled)
    stability = (
        "STABLE" if all(value == pooled_category for value in categories.values()) else "UNSTABLE"
    )
    luna_category = load_json(r23.POOLED)["pre_declared_readout"]
    write_new_json(
        ANALYSIS,
        {
            "schema": "study4x-sol-analysis-v1",
            "confirmatory": False,
            "study": "Study 4X-CM cross-model exploratory extension, gpt-5.6-sol arm, repeats 1-3",
            "model_id": MODEL_ID,
            "scope": "frozen DS=47 subset only; 3 repeats; single remote model",
            "evaluation_sha256": sha256_file(EVALUATION),
            "estimator": "task-equal mean of 47 within-task S-minus-Sprime differences, each condition mean over 3 repeats",
            "confidence_interval": "paired t 95% CI across 47 task differences",
            "p_value": "exact two-sided task-level sign-flip test (descriptive)",
            "pre_declared_readout": pooled_category,
            "pre_declared_stability_readout": stability,
            "per_repeat_readout": categories,
            "aggregates": pooled,
            "per_repeat_aggregates": per_repeat,
            "cross_arm_categorical_agreement": {
                "luna_pooled_readout": luna_category,
                "sol_pooled_readout": pooled_category,
                "agreement": "CONCORDANT" if luna_category == pooled_category else "DISCORDANT",
                "note": (
                    "Categorical agreement only. No difference of deltas, ratio, test, or "
                    "pooling across the two model arms is estimated; n = 2 models supports "
                    "a direction-agreement statement and nothing else."
                ),
            },
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
    print(
        f"cross-arm {'CONCORDANT' if luna_category == pooled_category else 'DISCORDANT'} "
        f"(luna {luna_category})",
        flush=True,
    )
    print(f"analysis sha256 {sha256_file(ANALYSIS)}", flush=True)


def main() -> None:
    stage = sys.argv[1]
    try:
        {"gates": gates, "generate": generate, "evaluate": evaluate, "analyze": analyze}[stage]()
    except BaseException as error:
        if isinstance(error, HardStop) and not HARD_STOP.exists():
            write_new_json(
                HARD_STOP, {"stage": stage, "error": str(error), "type": type(error).__name__}
            )
        raise


if __name__ == "__main__":
    main()
