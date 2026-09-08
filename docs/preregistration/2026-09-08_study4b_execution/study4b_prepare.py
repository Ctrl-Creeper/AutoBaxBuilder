#!/usr/bin/env python3
"""Mechanical Study-4B DS47 stimulus recovery and context audit."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

from tokenizers import Tokenizer


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
STUDY3 = HERE.parent / "2026-08-28_study3_execution"
STUDY4_CALIBRATION = HERE.parent / "2026-09-07_study4_calibration_execution"

BEGIN_SPEC = "<<<BEGIN SPECIFICATION S>>>"
END_SPEC = "<<<END SPECIFICATION S>>>"
CONTEXT_LIMIT = 262_144
MAX_OUTPUT_TOKENS = 8_192
WRAPPER_RESERVE = 128
REPEATS = 4
MODEL_ID = "Ornith-1.5-35B-A3B-Abliterated-MLX-4bit"
MODEL_FINGERPRINT = "3fe867b89aa52259573e963d121e8974128d5665367b30781d4419b71ef538de"

SOURCE_HASHES = {
    "ds_only_result_summary.json": "f46688507af7322fd2a077a5f138ef27c4fcac253394e7ad515da74e80cf81fb",
    "ds_derivation.json": "3377d187c2c37177f37e1c9b5d648b34468d10bd4239404b971888c835e4efe7",
    "eligibility_study3.json": "a9db938ba633bc400ac035d9a200501c8bb7c70986f9b38c2e964885f483f3a6",
    "sprime/sealed/_KEY_DO_NOT_SHOW_CODERS.json": "ecfc89e3515f68e526f31f68c4db06ad73035fff3f919e3a6419923e60a31fb8",
    "baseline/sealed/_KEY_DO_NOT_SHOW_CODERS.json": "88d74077e7949b45f7e6f131d283fa192937a4fbcf19d94c6b95031ebdd514e1",
    "writer_handoff/sealed/_KEY_DO_NOT_SHOW_WRITER.json": "3c9fc2925dd0511af5be6ebf27d2c1bf4ce6ab5b6d89937c5b74bffc73475106",
    "writer_handoff/submissions/writer_output_ACCEPT_FIRST_RUN2.json": "f2b0e73ab1d8b5efcb22bb53c2b8d026446994992195d9b55b483d8de593b49e",
    "sealed_materialization/FROZEN_CASE_MANIFEST.json": "2422431ac301aa4e439fe4ff2bdc7e23d6dfd2ffdf836cd8bdbda3ed25df2a36",
    "case_materialization_public.json": "8f1de14d1f01a35fb5dc33bec015a9143e4f297bf524bb6b48d9209c6c56555e",
}

STIMULI_PATH = HERE / "study4b_ds47_stimuli_SEALED.json"
READINESS_PATH = HERE / "study4b_readiness_manifest.json"
HASHES_PATH = HERE / "SHA256SUMS_READINESS"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def verify_sources() -> None:
    for relative, expected in SOURCE_HASHES.items():
        path = STUDY3 / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"Study-3 frozen source mismatch: {relative}")

    case_manifest = load_json(STUDY3 / "sealed_materialization/FROZEN_CASE_MANIFEST.json")
    data_path = Path(case_manifest["environment"]["pins"]["benchmark_data_json_path"])
    expected_data_hash = case_manifest["environment"]["pins"]["benchmark_data_json_sha256"]
    if not data_path.is_file() or sha256_file(data_path) != expected_data_hash:
        raise RuntimeError("Study-3 benchmark data source mismatch")


def verify_model_directory(
    model_dir: Path, expected_files: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    observed = [
        {
            "name": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(
            path
            for path in model_dir.iterdir()
            if path.is_file() and not path.name.startswith(".")
        )
    ]
    if observed != expected_files:
        raise RuntimeError("model directory or weights drift from frozen fingerprint")
    return observed


def extract_specification(packet_path: Path) -> str:
    text = packet_path.read_text()
    if text.count(BEGIN_SPEC) != 1 or text.count(END_SPEC) != 1:
        raise ValueError(f"{packet_path}: expected exactly one marker pair")
    before, remainder = text.split(BEGIN_SPEC, 1)
    specification, after = remainder.split(END_SPEC, 1)
    if before is None or after is None:
        raise ValueError(f"{packet_path}: expected exactly one marker pair")
    if not specification.startswith("\n") or not specification.endswith("\n"):
        raise ValueError(f"{packet_path}: specification is not line-delimited")
    return specification[1:-1]


def _unique_inverse(mapping: dict[str, dict[str, Any]], field: str) -> dict[int, str]:
    inverse: dict[int, str] = {}
    for task_id, row in mapping.items():
        index = int(row[field])
        if index in inverse:
            raise RuntimeError(f"duplicate source index in frozen key: {index}")
        inverse[index] = task_id
    return inverse


def restore_ds47_pairs() -> dict[str, Any]:
    verify_sources()
    ds_summary = load_json(STUDY3 / "ds_only_result_summary.json")
    q_key = load_json(STUDY3 / "sprime/sealed/_KEY_DO_NOT_SHOW_CODERS.json")
    p_key = load_json(STUDY3 / "baseline/sealed/_KEY_DO_NOT_SHOW_CODERS.json")
    writer_key = load_json(STUDY3 / "writer_handoff/sealed/_KEY_DO_NOT_SHOW_WRITER.json")
    writer_output = load_json(
        STUDY3 / "writer_handoff/submissions/writer_output_ACCEPT_FIRST_RUN2.json"
    )
    cases = load_json(STUDY3 / "sealed_materialization/FROZEN_CASE_MANIFEST.json")

    data_path = Path(cases["environment"]["pins"]["benchmark_data_json_path"])
    records = {int(row["index"]): row for row in load_json(data_path)}
    p_by_index = _unique_inverse(p_key["tasks"], "index")
    w_by_index = _unique_inverse(writer_key["tasks"], "index")

    ds_ids = ds_summary["ds_anonymous_task_ids"]
    if ds_summary.get("n_ds") != 47 or len(ds_ids) != 47 or len(set(ds_ids)) != 47:
        raise RuntimeError("frozen DS membership is not exactly 47 unique tasks")

    rows = []
    for q_id in ds_ids:
        if q_id not in q_key["tasks"]:
            raise RuntimeError(f"DS task absent from frozen S-prime key: {q_id}")
        index = int(q_key["tasks"][q_id]["index"])
        p_id = p_by_index[index]
        w_id = w_by_index[index]
        if w_id not in writer_output["tasks"]:
            raise RuntimeError(f"accepted writer output absent for source index {index}")
        if str(index) not in cases["tasks"] or index not in records:
            raise RuntimeError(f"frozen oracle or execution record absent for index {index}")

        s_run1_path = STUDY3 / f"baseline/run1_package/tasks/{p_id}.md"
        s_run2_path = STUDY3 / f"baseline/run2_package/tasks/{p_id}.md"
        sp_run1_path = STUDY3 / f"sprime/run1_package/tasks/{q_id}.md"
        sp_run2_path = STUDY3 / f"sprime/run2_package/tasks/{q_id}.md"
        s_run1 = extract_specification(s_run1_path)
        s_run2 = extract_specification(s_run2_path)
        sp_run1 = extract_specification(sp_run1_path)
        sp_run2 = extract_specification(sp_run2_path)
        if s_run1 != s_run2 or sp_run1 != sp_run2:
            raise RuntimeError(f"run1/run2 stimulus mismatch for {q_id}")

        oracle_cases = cases["tasks"][str(index)]["cases"]
        situations = [case["situation"] for case in oracle_cases]
        if situations != q_key["tasks"][q_id]["case_situations_source_order"]:
            raise RuntimeError(f"S-prime oracle ordering mismatch for {q_id}")
        if situations != p_key["tasks"][p_id]["case_situations_source_order"]:
            raise RuntimeError(f"baseline oracle ordering mismatch for {q_id}")

        record = records[index]
        execution = {
            "function_name": record["task_description"]["function_name"],
            "setup": record["unittest"]["setup"],
            "testcases": record["unittest"]["testcases"],
            "code_before": record["ground_truth"]["code_before"],
            "code_after": record["ground_truth"]["code_after"],
            "install_requires": record.get("install_requires", []),
        }
        rows.append(
            {
                "ds_task_id": q_id,
                "baseline_task_id": p_id,
                "writer_task_id": w_id,
                "source_index": index,
                "s": s_run1,
                "sprime": sp_run1,
                "oracle_cases": oracle_cases,
                "execution": execution,
                "s_sha256": sha256_bytes(s_run1.encode()),
                "sprime_sha256": sha256_bytes(sp_run1.encode()),
                "oracle_sha256": sha256_bytes(canonical_bytes(oracle_cases)),
                "execution_sha256": sha256_bytes(canonical_bytes(execution)),
                "s_run1_packet_sha256": sha256_file(s_run1_path),
                "s_run2_packet_sha256": sha256_file(s_run2_path),
                "sprime_run1_packet_sha256": sha256_file(sp_run1_path),
                "sprime_run2_packet_sha256": sha256_file(sp_run2_path),
                "s_run1_equals_run2": True,
                "sprime_run1_equals_run2": True,
                "oracle_matches_sealed_materialization": True,
            }
        )

    if len({row["source_index"] for row in rows}) != 47:
        raise RuntimeError("DS membership does not map to 47 unique source indices")
    return {
        "schema": "study4b-ds47-stimuli-v1",
        "scope": "Study-3 demonstrated-separable subset only",
        "source_hashes": SOURCE_HASHES,
        "benchmark_data_sha256": cases["environment"]["pins"][
            "benchmark_data_json_sha256"
        ],
        "n_pairs": len(rows),
        "pairs": rows,
    }


def fits_context(prompt_tokens: int) -> bool:
    return prompt_tokens + MAX_OUTPUT_TOKENS + WRAPPER_RESERVE <= CONTEXT_LIMIT


def build_readiness(stimuli: dict[str, Any]) -> dict[str, Any]:
    model_freeze = load_json(STUDY4_CALIBRATION / "pre_sample_freeze_manifest.json")
    if model_freeze["model"]["fingerprint_sha256"] != MODEL_FINGERPRINT:
        raise RuntimeError("frozen model fingerprint mismatch")
    model_dir = Path(model_freeze["model"]["directory"])
    observed_model_files = verify_model_directory(
        model_dir, model_freeze["model"]["files"]
    )
    if sha256_bytes(canonical_bytes(observed_model_files)) != MODEL_FINGERPRINT:
        raise RuntimeError("recomputed model fingerprint mismatch")
    tokenizer_entry = next(
        row for row in model_freeze["model"]["files"] if row["name"] == "tokenizer.json"
    )
    tokenizer_path = model_dir / "tokenizer.json"
    if sha256_file(tokenizer_path) != tokenizer_entry["sha256"]:
        raise RuntimeError("model tokenizer hash mismatch")
    tokenizer = Tokenizer.from_file(str(tokenizer_path))

    prompt_rows = []
    for row in stimuli["pairs"]:
        for condition, field in (("S", "s"), ("Sprime", "sprime")):
            count = len(tokenizer.encode(row[field]).ids)
            prompt_rows.append(
                {
                    "ds_task_id": row["ds_task_id"],
                    "source_index": row["source_index"],
                    "condition": condition,
                    "prompt_sha256": row[f"{field}_sha256"],
                    "prompt_tokens": count,
                    "required_context_tokens": count
                    + MAX_OUTPUT_TOKENS
                    + WRAPPER_RESERVE,
                    "fits_context": fits_context(count),
                }
            )

    over_limit = [row for row in prompt_rows if not row["fits_context"]]
    return {
        "schema": "study4b-execution-readiness-v1",
        "study_relation": {
            "fresh_sample_study4": "completed NO-GO at 0/160 validated pairs",
            "study4b": "conditional behavioral follow-up on frozen Study-3 DS47",
            "not_a_continuation_or_replacement": True,
        },
        "stimuli_sha256": sha256_bytes(canonical_bytes(stimuli)),
        "n_pairs": 47,
        "conditions": ["S", "Sprime"],
        "repeats_per_condition": REPEATS,
        "planned_requests": 47 * 2 * REPEATS,
        "model": {
            "id": MODEL_ID,
            "directory": str(model_dir),
            "fingerprint_sha256": MODEL_FINGERPRINT,
            "tokenizer_sha256": tokenizer_entry["sha256"],
        },
        "omlx": model_freeze["omlx"],
        "runtime": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "hardware_model": model_freeze["runtime"]["hardware_model"],
            "cpu_brand": model_freeze["runtime"]["cpu_brand"],
            "memory_bytes": model_freeze["runtime"]["memory_bytes"],
            "gpu_backend": "MLX on Apple Silicon unified-memory GPU",
        },
        "generation": {
            "system_prompt": None,
            "temperature": 0.2,
            "top_p": 1.0,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "chat_template_kwargs": {"enable_thinking": False},
            "fresh_request_per_completion": True,
            "conversation_state": None,
            "max_client_concurrency": 2,
        },
        "context": {
            "native_limit": CONTEXT_LIMIT,
            "wrapper_reserve": WRAPPER_RESERVE,
            "rule": "prompt_tokens + 8192 + 128 <= 262144",
            "n_prompts": len(prompt_rows),
            "over_limit_count": len(over_limit),
            "max_prompt_tokens": max(row["prompt_tokens"] for row in prompt_rows),
            "max_required_context_tokens": max(
                row["required_context_tokens"] for row in prompt_rows
            ),
            "rows": prompt_rows,
        },
        "analysis": {
            "task_difference": "d_t = mean_r(Y_sec[t,S,r]) - mean_r(Y_sec[t,Sprime,r])",
            "headline": "Delta_hat = sum_t(d_t) / 47",
            "ci": "paired t interval: Delta_hat +/- t_(0.975,46)*sd(d_t)/sqrt(47)",
            "test": "exact two-sided task-level sign-flip randomization test on d_t",
            "capability_guardrail": "same task-equal-weighted estimator using CapabilityPass",
            "joint_secondary": "same task-equal-weighted estimator using SecurityPass AND CapabilityPass",
            "completion_pooled_headline_forbidden": True,
        },
        "interpretation_boundary": (
            "Conditional effect on the Study-3 demonstrated-separable subset only; not a "
            "SeCodePLT-wide or fresh-sample effect."
        ),
        "go": len(over_limit) == 0,
    }


def write_new(path: Path, data: bytes) -> None:
    if path.exists():
        raise RuntimeError(f"refusing to overwrite frozen artifact: {path.name}")
    path.write_bytes(data)


def prepare() -> None:
    stimuli = restore_ds47_pairs()
    stimuli_bytes = json.dumps(stimuli, indent=2, ensure_ascii=False).encode() + b"\n"
    readiness = build_readiness(stimuli)
    readiness["stimuli_file_sha256"] = sha256_bytes(stimuli_bytes)
    readiness_bytes = json.dumps(readiness, indent=2, ensure_ascii=False).encode() + b"\n"

    write_new(STIMULI_PATH, stimuli_bytes)
    write_new(READINESS_PATH, readiness_bytes)
    hash_lines = (
        f"{sha256_file(Path(__file__))}  {Path(__file__).name}\n"
        f"{sha256_file(STIMULI_PATH)}  {STIMULI_PATH.name}\n"
        f"{sha256_file(READINESS_PATH)}  {READINESS_PATH.name}\n"
    ).encode()
    write_new(HASHES_PATH, hash_lines)
    print(
        json.dumps(
            {
                "n_pairs": readiness["n_pairs"],
                "over_limit_count": readiness["context"]["over_limit_count"],
                "max_prompt_tokens": readiness["context"]["max_prompt_tokens"],
                "planned_requests": readiness["planned_requests"],
                "go": readiness["go"],
                "stimuli_file_sha256": readiness["stimuli_file_sha256"],
                "readiness_sha256": sha256_file(READINESS_PATH),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    if sys.argv[1:] != ["prepare"]:
        raise SystemExit("usage: study4b_prepare.py prepare")
    prepare()
