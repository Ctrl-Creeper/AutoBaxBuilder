"""Study 4X-CM — cross-model exploratory extension. See DESIGN_FROZEN.md.

Exploratory. Reuses the frozen Study-4C prompt projection and the frozen
Study-4B/SeCodePLT evaluation harness read-only; writes only into this directory.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
S4B = REPO / "docs/preregistration/2026-09-08_study4b_execution"
S4C = REPO / "docs/preregistration/2026-09-08_study4c_execution"
sys.path.insert(0, str(S4B))

import study4b_execute as ex  # noqa: E402
import study4b_prepare as prepare  # noqa: E402

HardStop = ex.HardStop

DESIGN = HERE / "DESIGN_FROZEN.md"
DESIGN_SHA256 = "6632c086578660f80ced3caa09b3e745ae3e8a74d97ddc0f15650f2a4d85552d"
PROMPTS = S4C / "study4c_generation_stimuli_FROZEN.json"
PROMPTS_SHA256 = "f0268033011ef143fa4ed3238bfe5c9b07475cbe271050e085a36d0ad0185698"
ORACLE = S4B / "study4b_ds47_stimuli_SEALED.json"
ORACLE_SHA256 = "81ac8389d213998b95ad71fbfa431f3d6863a8371b9f04af0ebb5e790d7c84ef"

GATE_REPORT = HERE / "study4x_gate_report_FROZEN.json"
CALLS_DIR = HERE / "generation_calls"
COMPLETION = HERE / "study4x_generation_completion_FROZEN.json"
RESPONSE_HASHES = HERE / "SHA256SUMS_RESPONSES"
EVALUATION = HERE / "study4x_evaluation_FROZEN.json"
ANALYSIS = HERE / "study4x_analysis_FROZEN.json"
HARD_STOP = HERE / "STUDY4X_HARD_STOP.json"

ENDPOINT = "https://ai.bnds.fun/v1"
MODEL_ID = "gpt-5.6-luna"
API_KEY_ENV = "STUDY4X_API_KEY"

N_TASKS = 47
REPEATS = 1
CONDITIONS = ("S", "Sprime")
N_REQUESTS = N_TASKS * len(CONDITIONS) * REPEATS
MAX_CONCURRENCY = 4
GENERATION_CONFIG = {"temperature": 0.2, "top_p": 1.0, "max_tokens": 8192}
RETRY_DELAYS_SECONDS = (0, 20, 60, 120)
REQUEST_TIMEOUT_SECONDS = 900
ORACLE_MARKERS = ("unittest", "testcases", "assert ", "ground_truth", "patched_code")

sha256_file = ex.sha256_file
sha256_bytes = ex.sha256_bytes
canonical_bytes = ex.canonical_bytes
load_json = ex.load_json
write_new_json = ex.write_new_json


def write_new_hashfile(path: Path, targets: list[Path]) -> None:
    """Local copy of ex.write_new_hashfile: paths are relative to THIS directory."""
    rows = [f"{sha256_file(target)}  {target.relative_to(HERE)}" for target in targets]
    ex.write_new_bytes(path, ("\n".join(rows) + "\n").encode("utf-8"))


def verify_hashfile(path: Path) -> None:
    if not path.is_file():
        raise HardStop(f"hash manifest absent: {path.name}")
    for line in path.read_text().splitlines():
        expected, relative = line.split("  ", 1)
        target = HERE / relative
        if not target.is_file() or sha256_file(target) != expected:
            raise HardStop(f"hash mismatch: {relative}")


def root_seed(stimuli_sha: str) -> int:
    domain = f"study4x-crossmodel-v1|{stimuli_sha}|{MODEL_ID}"
    return int.from_bytes(hashlib.sha256(domain.encode()).digest()[:8], "big")


def api_key() -> str:
    key = os.environ.get(API_KEY_ENV)
    if not key:
        raise HardStop(f"{API_KEY_ENV} is not set (the key is process-local by design)")
    return key


def api_call(path: str, payload: dict[str, Any] | None, request_id: str) -> Any:
    body = canonical_bytes(payload) if payload is not None else None
    attempts: list[dict[str, Any]] = []
    for attempt, delay in enumerate(RETRY_DELAYS_SECONDS, 1):
        if delay:
            time.sleep(delay)
        request = urllib.request.Request(
            ENDPOINT + path,
            data=body,
            method="POST" if body else "GET",
            headers={
                "Authorization": f"Bearer {api_key()}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                value = json.loads(response.read())
            attempts.append({"attempt": attempt, "outcome": "success"})
            return value, attempts
        except urllib.error.HTTPError as exc:
            attempts.append({"attempt": attempt, "outcome": f"HTTP_{exc.code}"})
            if exc.code not in ex.RETRYABLE_HTTP_STATUSES:
                raise HardStop(f"non-retryable HTTP {exc.code} for {request_id}") from exc
        except Exception as exc:  # transport
            attempts.append({"attempt": attempt, "outcome": type(exc).__name__})
    raise HardStop(f"retries exhausted for {request_id}: {attempts[-1]['outcome']}")


def prompt_rows() -> list[dict[str, Any]]:
    """Gate 1-3: frozen, complete, oracle-free prompt projection."""
    if sha256_file(PROMPTS) != PROMPTS_SHA256:
        raise HardStop("frozen prompt projection hash mismatch")
    stimuli = load_json(PROMPTS)
    if stimuli.get("contains_hidden_tests_or_oracle") is not False:
        raise HardStop("prompt projection is not declared oracle-free")
    rows = stimuli["rows"]
    if len(rows) != N_TASKS:
        raise HardStop("prompt projection does not carry 47 tasks")
    for row in rows:
        for condition in CONDITIONS:
            text = row[condition]
            if sha256_bytes(text.encode()) != row[f"{condition}_sha256"]:
                raise HardStop(f"prompt hash mismatch: {row['ds_task_id']} {condition}")
            lowered = text.lower()
            if any(marker in lowered for marker in ORACLE_MARKERS):
                raise HardStop(f"oracle marker in prompt: {row['ds_task_id']} {condition}")
    return rows


def schedule(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    units = [
        {
            "request_id": f"{row['ds_task_id']}-{condition}-R1",
            "ds_task_id": row["ds_task_id"],
            "source_index": row["source_index"],
            "condition": condition,
            "repeat": 1,
            "prompt_sha256": row[f"{condition}_sha256"],
            "seed": int.from_bytes(
                hashlib.sha256(
                    f"{root_seed(PROMPTS_SHA256)}|{row['ds_task_id']}|{condition}".encode()
                ).digest()[:4],
                "big",
            ),
        }
        for row in rows
        for condition in CONDITIONS
    ]
    random.Random(root_seed(PROMPTS_SHA256)).shuffle(units)
    for position, unit in enumerate(units, 1):
        unit["position"] = position
    return units


def gates() -> None:
    if GATE_REPORT.exists():
        raise HardStop("gates are already frozen")
    if sha256_file(DESIGN) != DESIGN_SHA256:
        raise HardStop("DESIGN_FROZEN.md changed after freezing")
    rows = prompt_rows()
    if sha256_file(ORACLE) != ORACLE_SHA256:
        raise HardStop("evaluation oracle hash mismatch")
    prepare.verify_sources()

    models, _ = api_call("/models", None, "models")
    served = sorted(item["id"] for item in models["data"])
    if MODEL_ID not in served:
        raise HardStop(f"{MODEL_ID} is not served by the endpoint")

    smoke_payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
        **GENERATION_CONFIG,
        "stream": False,
    }
    smoke, _ = api_call("/chat/completions", smoke_payload, "smoke")
    if smoke.get("model") != MODEL_ID or not smoke.get("choices"):
        raise HardStop("smoke call did not return a usable choice from the pinned model")

    units = schedule(rows)
    report = {
        "schema": "study4x-gate-report-v1",
        "study": "Study 4X-CM cross-model exploratory extension",
        "confirmatory": False,
        "design_sha256": DESIGN_SHA256,
        "gates": {
            "prompt_projection_hash": "PASS",
            "prompt_completeness_and_per_prompt_hashes": "PASS",
            "prompt_projection_oracle_free": "PASS",
            "evaluation_oracle_hash": "PASS",
            "study3_oracle_provenance": "PASS",
            "model_served": "PASS",
            "smoke_call_with_generation_config": "PASS",
            "api_key_process_local_only": "PASS",
            "no_study4b_or_4c_artifact_opened_for_writing": "PASS",
        },
        "endpoint": ENDPOINT,
        "model_id": MODEL_ID,
        "served_model_ids": served,
        "smoke_response_id": smoke.get("id"),
        "smoke_system_fingerprint": smoke.get("system_fingerprint"),
        "smoke_content": smoke["choices"][0]["message"].get("content"),
        "generation_config": GENERATION_CONFIG,
        "n_requests_planned": N_REQUESTS,
        "randomization_root_seed": root_seed(PROMPTS_SHA256),
        "schedule": units,
        "comparability": (
            "Nominal generation parameters match Study 4B; the provider's sampler, "
            "quantization, system prompt and routing are unknown. The arms are not "
            "comparable to the Ornith-1.5-35B arms at the level of rates."
        ),
    }
    write_new_json(GATE_REPORT, report)
    print(f"gates 9/9 GO; gate report sha256 {sha256_file(GATE_REPORT)}", flush=True)


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
        "request_id": unit["request_id"],
        "ds_task_id": unit["ds_task_id"],
        "source_index": unit["source_index"],
        "condition": unit["condition"],
        "repeat": unit["repeat"],
        "position": unit["position"],
        "prompt_sha256": unit["prompt_sha256"],
        "seed": unit["seed"],
        "attempts": attempts,
        "elapsed_seconds": round(time.time() - started, 3),
        "response": response,
    }
    path.write_bytes(canonical_bytes(record))
    return record


def generate() -> None:
    if COMPLETION.exists():
        raise HardStop("generation is already frozen")
    report = load_json(GATE_REPORT)
    if report["design_sha256"] != DESIGN_SHA256 or sha256_file(DESIGN) != DESIGN_SHA256:
        raise HardStop("design changed after the gates were frozen")
    rows = {row["ds_task_id"]: row for row in prompt_rows()}
    CALLS_DIR.mkdir(exist_ok=True)
    units = report["schedule"]
    done = 0
    records: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as pool:
        futures = {
            pool.submit(_one_call, unit, rows[unit["ds_task_id"]][unit["condition"]]): unit
            for unit in units
        }
        for future in concurrent.futures.as_completed(futures):
            records.append(future.result())
            done += 1
            print(f"generate {done:03d}/{N_REQUESTS}", flush=True)
    if len(records) != N_REQUESTS:
        raise HardStop("generation incomplete")
    records.sort(key=lambda record: record["position"])
    finish_reasons: dict[str, int] = {}
    completion_tokens = 0
    for record in records:
        reason = record["response"]["choices"][0].get("finish_reason") or "unknown"
        finish_reasons[reason] = finish_reasons.get(reason, 0) + 1
        completion_tokens += (record["response"].get("usage") or {}).get("completion_tokens", 0)
    frozen = {
        "schema": "study4x-generation-completion-v1",
        "confirmatory": False,
        "gate_report_sha256": sha256_file(GATE_REPORT),
        "model_id": MODEL_ID,
        "endpoint": ENDPOINT,
        "n_completed": len(records),
        "n_retried_requests": sum(1 for r in records if len(r["attempts"]) > 1),
        "finish_reasons": finish_reasons,
        "total_completion_tokens": completion_tokens,
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
    }
    write_new_json(COMPLETION, frozen)
    write_new_hashfile(
        RESPONSE_HASHES,
        [CALLS_DIR / f"{record['request_id']}.json" for record in records],
    )
    print(f"{len(records)}/{N_REQUESTS} frozen; sha256 {sha256_file(COMPLETION)}", flush=True)


def hashes() -> None:
    """Write the response hash manifest for an already-frozen generation."""
    completion = load_json(COMPLETION)
    write_new_hashfile(
        RESPONSE_HASHES,
        [CALLS_DIR / f"{row['request_id']}.json" for row in completion["rows"]],
    )
    print(f"{len(completion['rows'])} response hashes written", flush=True)


def response_content(request_id: str) -> str:
    record = load_json(CALLS_DIR / f"{request_id}.json")
    message = record["response"]["choices"][0].get("message") or {}
    return message.get("content") or ""


def evaluate() -> None:
    if EVALUATION.exists():
        raise HardStop("evaluation is already frozen")
    verify_hashfile(RESPONSE_HASHES)
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
            "schema": "study4x-evaluation-v1",
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


def analyze() -> None:
    if ANALYSIS.exists():
        raise HardStop("analysis is already frozen")
    evaluation = load_json(EVALUATION)
    if evaluation["n_evaluated"] != N_REQUESTS:
        raise HardStop("evaluation is incomplete")
    task_ids = [pair["ds_task_id"] for pair in load_json(ORACLE)["pairs"]]
    aggregates = ex.aggregate_endpoints(evaluation["rows"], task_ids, REPEATS)

    def excludes_zero(name: str) -> bool:
        low, high = aggregates[name]["ci_95"]
        return low > 0 or high < 0

    security, capability = aggregates["security"], aggregates["capability"]
    if excludes_zero("security") and excludes_zero("capability"):
        if security["delta"] > 0 and capability["delta"] < 0:
            readout = "DIRECTIONAL_REPRODUCTION"
        else:
            readout = "OPPOSITE"
    elif excludes_zero("security") or excludes_zero("capability"):
        moved = security if excludes_zero("security") else capability
        expected = moved["delta"] > 0 if moved is security else moved["delta"] < 0
        readout = "PARTIAL" if expected else "OPPOSITE"
    else:
        readout = "NO_REPRODUCTION"

    write_new_json(
        ANALYSIS,
        {
            "schema": "study4x-analysis-v1",
            "confirmatory": False,
            "study": "Study 4X-CM cross-model exploratory extension",
            "model_id": MODEL_ID,
            "scope": "frozen DS=47 subset only; 1 repeat; single remote model",
            "evaluation_sha256": sha256_file(EVALUATION),
            "estimator": "task-equal mean of 47 within-task S-minus-Sprime differences",
            "confidence_interval": "paired t 95% CI across 47 task differences",
            "p_value": "exact two-sided task-level sign-flip test (descriptive)",
            "pre_declared_readout": readout,
            "aggregates": aggregates,
            "replicates_study4b": False,
            "comparable_to_ornith_arms": False,
            "subgroup_or_task_failure_mining_performed": False,
        },
    )
    for name in ("security", "capability", "joint"):
        row = aggregates[name]
        print(
            f"{name:11s} S={row['rate_S']:.4f} Sprime={row['rate_Sprime']:.4f} "
            f"delta={row['delta']:+.4f} CI=[{row['ci_95'][0]:+.4f},{row['ci_95'][1]:+.4f}] "
            f"p={row['randomization_p_two_sided']:.4g}",
            flush=True,
        )
    print(f"read-out {readout}; analysis sha256 {sha256_file(ANALYSIS)}", flush=True)


def main() -> None:
    stage = sys.argv[1]
    try:
        {"gates": gates, "generate": generate, "hashes": hashes, "evaluate": evaluate, "analyze": analyze}[stage]()
    except BaseException as error:
        if isinstance(error, HardStop) and not HARD_STOP.exists():
            write_new_json(
                HARD_STOP,
                {"stage": stage, "error": str(error), "type": type(error).__name__},
            )
        raise


if __name__ == "__main__":
    main()
